import Tag from './ui/Tag'

const VARIANTES = { green: 'sucesso', red: 'erro', yellow: 'aviso', purple: 'violeta', gray: 'neutro' }

export default function Badge({ color = 'gray', children }) {
  return <Tag variante={VARIANTES[color]}>{children}</Tag>
}
