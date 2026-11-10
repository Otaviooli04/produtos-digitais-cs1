import { useState } from 'react'
import { Plus } from 'lucide-react'
import Spinner from './Spinner'
import Botao from './ui/Botao'

const STRUCTURES = ['If', 'For', 'While', 'DoWhile', 'Switch']

export default function QuestionForm({ initial, onSubmit, onCancel, saving, isEdit }) {
  const [number, setNumber] = useState(initial?.number ?? '')
  const [points, setPoints] = useState(initial?.points ?? 1)
  const [statement, setStatement] = useState(initial?.statement ?? '')
  const [required, setRequired] = useState(initial?.required_structures ?? [])
  const [forbidden, setForbidden] = useState(initial?.forbidden_structures ?? [])
  const [requiresLoop, setRequiresLoop] = useState(initial?.requires_loop ?? false)
  const [functions, setFunctions] = useState(initial?.required_functions ?? [])

  const toggle = (list, setList, value) =>
    setList(list.includes(value) ? list.filter(v => v !== value) : [...list, value])

  const addFunction = () => setFunctions([...functions, {
    name: '', param_count: null, return_type: null,
    requires_recursion: false, requires_pointer_param: false,
  }])
  const updateFunction = (i, patch) =>
    setFunctions(functions.map((f, idx) => idx === i ? { ...f, ...patch } : f))
  const removeFunction = (i) => setFunctions(functions.filter((_, idx) => idx !== i))

  const submit = (e) => {
    e.preventDefault()
    if (!number.trim()) return
    onSubmit({
      number: number.trim(),
      points: points === '' || points == null ? 1 : Number(points),
      statement: statement.trim(),
      required_structures: required,
      forbidden_structures: forbidden,
      requires_loop: requiresLoop,
      required_functions: functions
        .filter(f => f.name.trim())
        .map(f => ({
          name: f.name.trim(),
          param_count: f.param_count === '' || f.param_count == null ? null : Number(f.param_count),
          return_type: f.return_type?.trim() || null,
          requires_recursion: !!f.requires_recursion,
          requires_pointer_param: !!f.requires_pointer_param,
        })),
    })
  }

  return (
    <form onSubmit={submit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1">Número da questão</label>
          <input
            type="text" value={number} onChange={e => setNumber(e.target.value)}
            disabled={isEdit}
            className="campo disabled:bg-lavanda disabled:text-cinza-texto"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1">Valor da questão</label>
          <input
            type="number" min="0" step="0.1" value={points}
            onChange={e => setPoints(e.target.value)}
            className="campo"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-bold text-cinza-texto mb-1">Enunciado</label>
        <textarea
          value={statement} onChange={e => setStatement(e.target.value)} rows={6}
          className="campo"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Estruturas exigidas</label>
          <div className="flex flex-wrap gap-1.5">
            {STRUCTURES.map(s => (
              <button type="button" key={s} onClick={() => toggle(required, setRequired, s)}
                aria-pressed={required.includes(s)}
                className={`min-h-11 text-xs font-bold px-3 py-1 rounded-botao border-2 ${
                  required.includes(s) ? 'border-violeta bg-lavanda text-violeta' : 'border-noite/20 text-cinza-texto hover:border-noite hover:bg-lavanda'}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-bold text-cinza-texto mb-1.5">Estruturas proibidas</label>
          <div className="flex flex-wrap gap-1.5">
            {STRUCTURES.map(s => (
              <button type="button" key={s} onClick={() => toggle(forbidden, setForbidden, s)}
                aria-pressed={forbidden.includes(s)}
                className={`min-h-11 text-xs font-bold px-3 py-1 rounded-botao border-2 ${
                  forbidden.includes(s) ? 'border-erro bg-erro-fundo text-erro' : 'border-noite/20 text-cinza-texto hover:border-noite hover:bg-lavanda'}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-cinza-texto">
        <input type="checkbox" checked={requiresLoop} onChange={e => setRequiresLoop(e.target.checked)}
          className="w-4 h-4 accent-violeta" />
        Exige laço de repetição
      </label>

      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-xs font-bold text-cinza-texto">Funções exigidas</label>
          <button type="button" onClick={addFunction} className="inline-flex items-center gap-1 min-h-11 px-2 text-xs font-bold text-violeta hover:underline">
            <Plus className="w-4 h-4" aria-hidden="true" />
            função
          </button>
        </div>
        <div className="space-y-2">
          {functions.map((f, i) => (
            <div key={i} className="rounded-botao border-2 border-noite/20 p-3 space-y-2">
              <div className="flex flex-wrap gap-2">
                <input type="text" placeholder="nome" value={f.name}
                  onChange={e => updateFunction(i, { name: e.target.value })}
                  className="campo flex-1 min-w-32" />
                <input type="number" placeholder="nº params" value={f.param_count ?? ''}
                  onChange={e => updateFunction(i, { param_count: e.target.value })}
                  className="campo w-24!" />
                <input type="text" placeholder="retorno" value={f.return_type ?? ''}
                  onChange={e => updateFunction(i, { return_type: e.target.value })}
                  className="campo w-24!" />
                <button type="button" onClick={() => removeFunction(i)}
                  className="min-h-11 px-2 text-xs font-bold text-erro hover:bg-erro-fundo rounded-botao">remover</button>
              </div>
              <div className="flex gap-4 text-xs text-cinza-texto">
                <label className="flex items-center gap-1.5">
                  <input type="checkbox" checked={!!f.requires_recursion}
                    onChange={e => updateFunction(i, { requires_recursion: e.target.checked })}
                    className="w-4 h-4 accent-violeta" />
                  recursiva
                </label>
                <label className="flex items-center gap-1.5">
                  <input type="checkbox" checked={!!f.requires_pointer_param}
                    onChange={e => updateFunction(i, { requires_pointer_param: e.target.checked })}
                    className="w-4 h-4 accent-violeta" />
                  usa ponteiro
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <Botao variante="secundario" onClick={onCancel}>
          Cancelar
        </Botao>
        <Botao type="submit" disabled={saving || !number.trim()}>
          {saving && <Spinner className="w-4 h-4" />}
          {isEdit ? 'Salvar' : 'Adicionar'}
        </Botao>
      </div>
    </form>
  )
}
