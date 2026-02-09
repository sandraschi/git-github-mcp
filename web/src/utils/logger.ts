type LogLevel = 'info' | 'warn' | 'error' | 'debug'

export interface LogEntry {
  timestamp: string
  level: LogLevel
  message: string
  context?: Record<string, unknown>
}

type Listener = (entry: LogEntry) => void

const listeners = new Set<Listener>()

function emit(level: LogLevel, message: string, context?: Record<string, unknown>) {
  const entry: LogEntry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    context,
  }
  listeners.forEach((fn) => fn(entry))
}

export const logger = {
  info: (msg: string, ctx?: Record<string, unknown>) => emit('info', msg, ctx),
  warn: (msg: string, ctx?: Record<string, unknown>) => emit('warn', msg, ctx),
  error: (msg: string, ctx?: Record<string, unknown>) => emit('error', msg, ctx),
  debug: (msg: string, ctx?: Record<string, unknown>) => emit('debug', msg, ctx),
  on: (fn: Listener) => { listeners.add(fn); return () => listeners.delete(fn) },
  off: (fn: Listener) => listeners.delete(fn),
}
