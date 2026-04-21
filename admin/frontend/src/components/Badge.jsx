const variants = {
  active:   'bg-green-100 text-green-700',
  pending:  'bg-yellow-100 text-yellow-700',
  paused:   'bg-gray-100 text-gray-600',
  base:     'bg-green-100 text-green-700',
  light:    'bg-yellow-100 text-yellow-700',
  recovery: 'bg-orange-100 text-orange-700',
  rest:     'bg-gray-100 text-gray-500',
  done:     'bg-green-100 text-green-700',
  partial:  'bg-yellow-100 text-yellow-700',
  skipped:  'bg-red-100 text-red-600',
  default:  'bg-gray-100 text-gray-600',
}

export default function Badge({ value, label }) {
  const cls = variants[value] ?? variants.default
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {label ?? value}
    </span>
  )
}
