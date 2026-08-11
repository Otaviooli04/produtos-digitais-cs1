import Modal from './Modal'
import Spinner from './Spinner'

export default function ConfirmDialog({
  open, onClose, onConfirm, title = 'Confirmar',
  message, confirmLabel = 'Excluir', loading = false, danger = true,
}) {
  return (
    <Modal open={open} onClose={loading ? () => {} : onClose} title={title}>
      <p className="text-sm text-gray-600 mb-5 whitespace-pre-wrap">{message}</p>
      <div className="flex justify-end gap-2">
        <button
          onClick={onClose}
          disabled={loading}
          className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 disabled:opacity-40 transition-colors"
        >
          Cancelar
        </button>
        <button
          onClick={onConfirm}
          disabled={loading}
          className={`inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg text-white disabled:opacity-40 transition-colors ${
            danger ? 'bg-red-600 hover:bg-red-700' : 'bg-purple-600 hover:bg-purple-700'
          }`}
        >
          {loading && <Spinner className="w-4 h-4" />}
          {confirmLabel}
        </button>
      </div>
    </Modal>
  )
}
