!macro KillProcesses
  DetailPrint "Stopping processes..."
  ExecWait 'taskkill /F /IM "git-github-mcp-backend.exe" /T' $0
  ExecWait 'taskkill /F /IM "git-github-mcp-native.exe" /T' $0
  Sleep 2000
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_POSTINSTALL
  IfFileExists "$INSTDIR\resources\install-mcp-clients.ps1" 0 mcp_hook_done
    DetailPrint "Register MCP server in Cursor / Claude Desktop"
    ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$INSTDIR\resources\install-mcp-clients.ps1" -Interactive'
  mcp_hook_done:
!macroend

!macro NSIS_HOOK_PREINSTALL
  !insertmacro KillProcesses
!macroend

!macro NSIS_HOOK_PREUNINSTALL
  !insertmacro KillProcesses
!macroend
