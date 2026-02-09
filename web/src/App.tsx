import { useState, useEffect } from 'react'
import { logger, type LogEntry } from './utils/logger'
import { Layout } from './components/layout/Layout'
import { HelpModal } from './components/modals/HelpModal'
import { LoggerModal } from './components/modals/LoggerModal'
import { Dashboard } from './pages/Dashboard'
import { Repos } from './pages/Repos'
import { Issues } from './pages/Issues'
import { PRs } from './pages/PRs'
import { Tools } from './pages/Tools'
import { Glama } from './pages/Glama'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [showLogger, setShowLogger] = useState(false)
  const [showHelp, setShowHelp] = useState(false)
  const [logs, setLogs] = useState<string[]>([])

  useEffect(() => {
    const handleLog = (entry: LogEntry) => {
      const ts = new Date(entry.timestamp).toLocaleTimeString()
      const ctx = entry.context ? ` ${JSON.stringify(entry.context)}` : ''
      setLogs((prev) => [...prev, `[${ts}] [${entry.level}] ${entry.message}${ctx}`])
    }
    const unsub = logger.on(handleLog)

    const handleKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault()
        setShowLogger((s) => !s)
      }
      if (e.key === '?' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        setShowHelp(true)
      }
    }
    window.addEventListener('keydown', handleKey)
    return () => {
      unsub()
      window.removeEventListener('keydown', handleKey)
    }
  }, [])

  const pages: Record<string, React.ReactNode> = {
    dashboard: <Dashboard />,
    repos: <Repos />,
    glama: <Glama />,
    issues: <Issues />,
    prs: <PRs />,
    tools: <Tools />,
  }

  return (
    <>
      <Layout
        currentPage={currentPage}
        onNavigate={setCurrentPage}
        onShowLogger={() => setShowLogger(true)}
        onShowHelp={() => setShowHelp(true)}
      >
        {pages[currentPage] || <Dashboard />}
      </Layout>

      <HelpModal isOpen={showHelp} onClose={() => setShowHelp(false)} />
      <LoggerModal isOpen={showLogger} onClose={() => setShowLogger(false)} logs={logs} />
    </>
  )
}

export default App
