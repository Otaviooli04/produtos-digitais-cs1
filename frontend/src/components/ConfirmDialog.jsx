import Modal from './Modal'
import Spinner from './Spinner'

export default function ConfirmDialog({
  open, onClose, onConfirm, title = 'Confirmar',
  message, confirmLabel = 'Excluir', loading = false, danger = true,
}) {
  return (
    <Modal open={open} onClose={loading ? () => {} : onClose} title={title}>
      <p className="text-sm text-cinza-texto mb-5 whitespace-pre-wrap">{message}</p>
      <div className="flex justify-end gap-2">
        <button
          onClick={onClose}
          disabled={loading}
          className="text-sm px-4 py-2 rounded-lg border border-noite/20 text-cinza-texto hover:bg-lavanda disabled:opacity-40 transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className={`inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg text-white disabled:opacity-40 transition-colors ${
            danger ? 'bg-erro hover:bg-erro' : 'bg-violeta hover:bg-violeta-escuro'
          }`}
        >
          {loading && <Spinner className="w-4 h-4" />}
          {confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
