import { X } from 'lucide-react'

interface LoggerModalProps {
  isOpen: boolean
  onClose: () => void
  logs: string[]
}

export function LoggerModal({ isOpen, onClose, logs }: LoggerModalProps) {
  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        className="bg-[#12121a] border border-[#1e1e2e] rounded-xl shadow-2xl w-full max-w-2xl mx-4 max-h-[70vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-[#1e1e2e]">
          <h2 className="text-lg font-semibold text-slate-200">Logger</h2>
          <button onClick={onClose} className="p-2 rounded-lg text-slate-500 hover:text-slate-200 hover:bg-slate-800/50">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-4 font-mono text-xs text-slate-400 space-y-1">
          {logs.length === 0 ? (
            <p className="text-slate-500">No logs yet</p>
          ) : (
            logs.slice(-200).map((line, i) => (
              <div key={i} className="break-all">
                {line}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
