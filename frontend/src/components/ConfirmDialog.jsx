import Modal from './Modal'
import Spinner from './Spinner'
import Botao from './ui/Botao'

export default function ConfirmDialog({
  open, onClose, onConfirm, title = 'Confirmar',
  message, confirmLabel = 'Excluir', loading = false, danger = true,
}) {
  return (
    <Modal open={open} onClose={loading ? () => {} : onClose} title={title}>
      <p className="text-sm text-cinza-texto mb-5 whitespace-pre-wrap">{message}</p>
      <div className="flex justify-end gap-2">
        <Botao variante="secundario" onClick={onClose} disabled={loading}>
          Cancelar
        </Botao>
        <Botao variante={danger ? 'perigo' : 'primario'} onClick={onConfirm} disabled={loading}>
          {loading && <Spinner className="w-4 h-4" />}
          {confirmLabel}
        </Botao>
      </div>
    </Modal>
  )
}
