use std::fs::{self, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use std::thread;
use std::time::Duration;

use tauri::path::BaseDirectory;
use tauri::{AppHandle, Emitter, Manager};

pub struct BackendProcess(pub Mutex<Option<Child>>);

const BACKEND_PORT: u16 = 10713;
const FRONTEND_PORT: u16 = 10714;

fn dev_backend_path() -> Option<PathBuf> {
    if !cfg!(debug_assertions) {
        return None;
    }
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("binaries")
        .join("git-github-mcp-backend-x86_64-pc-windows-msvc.exe");
    path.exists().then_some(path)
}

fn log_line(app: &AppHandle, message: &str) {
    eprintln!("[backend] {message}");
    if let Ok(dir) = app.path().app_log_dir() {
        let _ = fs::create_dir_all(&dir);
        let log_path = dir.join("backend-spawn.log");
        if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_path) {
            let _ = writeln!(file, "{message}");
        }
    }
}

fn resolve_bundled_backend(app: &AppHandle) -> Result<PathBuf, String> {
    let mut tried = Vec::new();

    if let Ok(path) = app.path().resolve(BACKEND_NAME, BaseDirectory::Resource) {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(path) = app
        .path()
        .resolve("resources/git-github-mcp-backend.exe", BaseDirectory::Resource)
    {
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    if let Ok(dir) = app.path().executable_dir() {
        let path = dir.join("resources").join(BACKEND_NAME);
        tried.push(path.display().to_string());
        if path.exists() {
            return Ok(path);
        }
    }

    Err(format!(
        "bundled backend missing from resources (tried: {})",
        tried.join("; ")
    ))
}

const BACKEND_NAME: &str = "git-github-mcp-backend.exe";

fn install_dir_from_backend(path: &PathBuf) -> PathBuf {
    if let Some(parent) = path.parent() {
        if parent
            .file_name()
            .is_some_and(|name| name.eq_ignore_ascii_case("resources"))
        {
            if let Some(install_dir) = parent.parent() {
                return install_dir.to_path_buf();
            }
        }
        return parent.to_path_buf();
    }
    PathBuf::from(".")
}

pub fn materialize_backend(app: &AppHandle) -> Result<PathBuf, String> {
    if let Some(dev_path) = dev_backend_path() {
        log_line(app, &format!("using dev backend: {}", dev_path.display()));
        return Ok(dev_path);
    }

    let bundled = resolve_bundled_backend(app)?;
    log_line(
        app,
        &format!("using bundled backend: {}", bundled.display()),
    );
    // Strip Windows extended-length prefix
    let s = bundled.to_string_lossy().to_string();
    let clean = s.strip_prefix("\\\\?\\").map(PathBuf::from).unwrap_or(bundled.clone());
    Ok(clean)
}

fn is_port_in_use(port: u16) -> bool {
    // Cheap TCP connect test - if we can connect, someone is listening
    let addr = format!("127.0.0.1:{port}");
    if let Ok(addrs) = addr.to_socket_addrs() {
        for a in addrs {
            if TcpStream::connect_timeout(&a, Duration::from_millis(300)).is_ok() {
                return true;
            }
        }
    }
    false
}

fn is_backend_healthy(port: u16) -> bool {
    // Use a tiny blocking http check via raw TCP HTTP
    if let Ok(mut stream) = TcpStream::connect_timeout(
        &format!("127.0.0.1:{port}").to_socket_addrs().unwrap().next().unwrap(),
        Duration::from_millis(400),
    ) {
        let req = format!("GET /health HTTP/1.0\r\nHost: 127.0.0.1:{port}\r\n\r\n");
        let _ = stream.write_all(req.as_bytes());
        let mut buf = [0u8; 512];
        if let Ok(n) = std::io::Read::read(&mut stream, &mut buf) {
            let resp = String::from_utf8_lossy(&buf[..n]);
            return resp.contains("200") || resp.contains("\"ok\":true") || resp.contains("ok");
        }
    }
    false
}

fn show_collision_dialog(app: &AppHandle, title: &str, msg: &str) {
    log_line(app, &format!("COLLISION: {title} - {msg}"));
    // Try Tauri dialog, fall back to log
    #[allow(unused)]
    {
        use tauri_plugin_dialog::DialogExt;
        let _ = app.dialog().message(msg).title(title).blocking_show();
    }
    let _ = app.emit("backend-status", format!("warning: {msg}"));
}

fn free_port_if_stale(port: u16, app: &AppHandle) {
    if is_backend_healthy(port) {
        log_line(app, &format!("port {port} healthy - not killing (dev server reuse)"));
        return;
    }
    if !is_port_in_use(port) {
        return;
    }
    log_line(app, &format!("port {port} stale (no health) - freeing"));
    #[cfg(windows)]
    {
        let script = format!(
            "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | ForEach-Object {{ taskkill /F /PID $_.OwningProcess /T 2>$null }}"
        );
        let _ = Command::new("powershell.exe")
            .args(["-NoProfile", "-Command", &script])
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .status();
        thread::sleep(Duration::from_millis(300));
    }
}

fn stop_managed_child(state: &BackendProcess) {
    if let Some(mut child) = state.0.lock().unwrap().take() {
        let _ = child.kill();
        let _ = child.wait();
    }
}

pub fn spawn_backend(app: AppHandle, state: &BackendProcess) -> Result<String, String> {
    // Reverse collision: dev start.bat already holds 10713/10714 ?
    if is_backend_healthy(BACKEND_PORT) {
        let msg = format!(
            "Dev server already running on 127.0.0.1:{BACKEND_PORT} (health OK). Using existing backend instead of starting a second one.\n\nClose the dev server (stop.bat) before starting the desktop app if you want the Tauri-embedded backend."
        );
        show_collision_dialog(
            &app,
            "Port collision — dev server holds 10713",
            &msg,
        );
        log_line(&app, &format!("reusing existing backend on {BACKEND_PORT}, not spawning"));
        return Ok(format!("Reusing existing backend on port {BACKEND_PORT}"));
    }
    // Also warn if frontend dev vite holds 10714 (beforeDevCommand would collide)
    if is_port_in_use(FRONTEND_PORT) && cfg!(debug_assertions) {
        let msg = format!(
            "Frontend dev server already on :{FRONTEND_PORT}. Tauri devUrl http://localhost:{FRONTEND_PORT} will collide.\n\nClose the dev start.bat (or stop vite) before `cargo tauri dev`."
        );
        show_collision_dialog(&app, "Port collision — dev frontend holds 10714", &msg);
        log_line(&app, "frontend 10714 in use - devUrl collision warning shown");
    }

    // Only free stale holders, not healthy dev
    free_port_if_stale(BACKEND_PORT, &app);
    stop_managed_child(state);

    let backend_path = materialize_backend(&app)?;
    let workdir = app
        .path()
        .executable_dir()
        .ok()
        .unwrap_or_else(|| install_dir_from_backend(&backend_path));

    log_line(
        &app,
        &format!(
            "spawning {} (cwd {}) on port {BACKEND_PORT}",
            backend_path.display(),
            workdir.display()
        ),
    );

    let mut command = Command::new(&backend_path);
    command
        .current_dir(&workdir)
        .env("MCP_PORT", BACKEND_PORT.to_string())
        .env("MCP_HOST", "127.0.0.1")
        .env("GIT_GITHUB_MCP_TAURI", "1")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        const CREATE_NO_WINDOW: u32 = 0x0800_0000;
        command.creation_flags(CREATE_NO_WINDOW);
    }

    let mut child = command
        .spawn()
        .map_err(|e| format!("Failed to spawn {}: {e}", backend_path.display()))?;

    let stdout = child.stdout.take();
    let stderr = child.stderr.take();
    state.0.lock().unwrap().replace(child);

    if let Some(out) = stdout {
        let app_handle = app.clone();
        thread::spawn(move || watch_backend_stream(out, app_handle));
    }
    if let Some(err) = stderr {
        let app_handle = app.clone();
        thread::spawn(move || watch_backend_stream(err, app_handle));
    }

    Ok(format!("Backend starting on port {BACKEND_PORT}"))
}

fn watch_backend_stream<R: std::io::Read + Send + 'static>(stream: R, app: AppHandle) {
    let reader = BufReader::new(stream);
    let mut ready = false;
    for line in reader.lines().map_while(Result::ok) {
        log_line(&app, &line);
        if !ready
            && (line.contains("Uvicorn running") || line.contains("Application startup complete"))
        {
            ready = true;
            let _ = app.emit("backend-status", "ready");
        }
    }
}
