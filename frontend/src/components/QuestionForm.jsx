import { useState } from 'react'
import Spinner from './Spinner'

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
          <label className="block text-xs font-medium text-gray-500 mb-1">Número da questão</label>
          <input
            type="text" value={number} onChange={e => setNumber(e.target.value)}
            disabled={isEdit}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 disabled:bg-gray-50 disabled:text-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Valor da questão</label>
          <input
            type="number" min="0" step="0.1" value={points}
            onChange={e => setPoints(e.target.value)}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Enunciado</label>
        <textarea
          value={statement} onChange={e => setStatement(e.target.value)} rows={6}
          className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Estruturas exigidas</label>
          <div className="flex flex-wrap gap-1.5">
            {STRUCTURES.map(s => (
              <button type="button" key={s} onClick={() => toggle(required, setRequired, s)}
                className={`text-xs px-2 py-1 rounded-md border transition-colors ${
                  required.includes(s) ? 'border-purple-400 bg-purple-50 text-purple-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1.5">Estruturas proibidas</label>
          <div className="flex flex-wrap gap-1.5">
            {STRUCTURES.map(s => (
              <button type="button" key={s} onClick={() => toggle(forbidden, setForbidden, s)}
                className={`text-xs px-2 py-1 rounded-md border transition-colors ${
                  forbidden.includes(s) ? 'border-red-400 bg-red-50 text-red-700' : 'border-gray-200 text-gray-500 hover:bg-gray-50'}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      <label className="flex items-center gap-2 text-sm text-gray-700">
        <input type="checkbox" checked={requiresLoop} onChange={e => setRequiresLoop(e.target.checked)}
          className="rounded border-gray-300 text-purple-600 focus:ring-purple-500" />
        Exige laço de repetição
      </label>

      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className="text-xs font-medium text-gray-500">Funções exigidas</label>
          <button type="button" onClick={addFunction} className="text-xs text-purple-600 hover:underline">+ função</button>
        </div>
        <div className="space-y-2">
          {functions.map((f, i) => (
            <div key={i} className="rounded-lg border border-gray-200 p-3 space-y-2">
              <div className="flex gap-2">
                <input type="text" placeholder="nome" value={f.name}
                  onChange={e => updateFunction(i, { name: e.target.value })}
                  className="flex-1 text-sm rounded-md border border-gray-200 px-2 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500" />
                <input type="number" placeholder="nº params" value={f.param_count ?? ''}
                  onChange={e => updateFunction(i, { param_count: e.target.value })}
                  className="w-24 text-sm rounded-md border border-gray-200 px-2 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500" />
                <input type="text" placeholder="retorno" value={f.return_type ?? ''}
                  onChange={e => updateFunction(i, { return_type: e.target.value })}
                  className="w-24 text-sm rounded-md border border-gray-200 px-2 py-1 focus:outline-none focus:ring-1 focus:ring-purple-500" />
                <button type="button" onClick={() => removeFunction(i)}
                  className="text-xs text-red-500 hover:text-red-700 px-1">remover</button>
              </div>
              <div className="flex gap-4 text-xs text-gray-600">
                <label className="flex items-center gap-1.5">
                  <input type="checkbox" checked={!!f.requires_recursion}
                    onChange={e => updateFunction(i, { requires_recursion: e.target.checked })}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500" />
                  recursiva
                </label>
                <label className="flex items-center gap-1.5">
                  <input type="checkbox" checked={!!f.requires_pointer_param}
                    onChange={e => updateFunction(i, { requires_pointer_param: e.target.checked })}
                    className="rounded border-gray-300 text-purple-600 focus:ring-purple-500" />
                  usa ponteiro
                </label>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end gap-2 pt-1">
        <button type="button" onClick={onCancel}
          className="text-sm px-4 py-2 rounded-lg border border-gray-200 text-gray-700 hover:bg-gray-50 transition-colors">
          Cancelar
        </button>
        <button type="submit" disabled={saving || !number.trim()}
          className="inline-flex items-center gap-2 text-sm px-4 py-2 rounded-lg bg-purple-600 text-white hover:bg-purple-700 disabled:opacity-40 transition-colors">
          {saving && <Spinner className="w-4 h-4" />}
          {isEdit ? 'Salvar' : 'Adicionar'}
        </button>
      </div>
    </form>
  )
}
