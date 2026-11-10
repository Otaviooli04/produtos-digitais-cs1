import { useEffect } from 'react'
import { X } from 'lucide-react'

export default function Modal({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-noite/40"
      onClick={onClose}
    >
      <div
        className="bg-white border-2 border-noite rounded-card shadow-bloco max-w-2xl w-full max-h-[80vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between gap-3 pl-6 pr-2 py-2 border-b-2 border-noite/10">
          <h2 className="titulo-card text-lg!">{title}</h2>
          <button
            onClick={onClose}
            className="inline-flex items-center justify-center min-h-11 min-w-11 rounded-botao border-2 border-transparent text-noite hover:border-noite hover:bg-lavanda"
            aria-label="Fechar"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto">{children}</div>
      </div>
    </div>
  )
}
