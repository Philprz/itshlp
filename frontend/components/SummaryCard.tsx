import { Card } from '@/components/ui/card'

interface SummaryCardProps {
  content: string
  format: 'Summary' | 'Guide'
  isGpt: boolean
}

export default function SummaryCard({ content, format, isGpt }: SummaryCardProps) {
  const badge = isGpt
    ? <span className="text-xs bg-yellow-400 text-white px-2 py-1 rounded">🧠 source: GPT</span>
    : <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">📁 source: Tickets</span>

  const title = format === 'Summary' ? '📝 Résumé global' : '🛠️ Guide pratique'

  return (
    <Card className="bg-white dark:bg-gray-900 border-l-4 border-blue-600 p-6 space-y-4 rounded-xl shadow-sm">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        {badge}
      </div>
      <p className="text-sm text-gray-700 dark:text-gray-200 whitespace-pre-wrap">{content}</p>
    </Card>
  )
}
