import { Badge } from '@/components/ui/badge'

interface MetaBadgeProps {
  meta: any;
}

export default function MetaBadge({ meta }: MetaBadgeProps) {
  if (!meta) return null;

  const dateFilter = meta.dateFilter?.gte
    ? new Date(meta.dateFilter.gte * 1000).toLocaleDateString()
    : null;

  return (
    <div className="flex flex-wrap items-center gap-2 mb-4">
      {meta.use_embedding && (
        <Badge className="bg-blue-100 text-blue-800 border border-blue-300">
          🔍 Recherche vectorielle activée
        </Badge>
      )}
      {meta.mode === 'deepresearch' && (
        <Badge className="bg-green-100 text-green-800 border border-green-300">
          🤖 Recherche GPT enrichie
        </Badge>
      )}
      {dateFilter && (
        <Badge className="bg-cyan-100 text-cyan-800 border border-cyan-300">
          ⏱️ Filtré après le {dateFilter}
        </Badge>
      )}
    </div>
  );
}
