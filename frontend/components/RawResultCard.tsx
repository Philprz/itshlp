// --- RAW RESULT CARD ---
'use client'

import { Card } from "@/components/ui/card"
import { Badge } from "./ui/badge"
import { ExternalLink } from "lucide-react"
import { useEffect, useState } from "react"
import useCharLimit from '@/hooks/useCharLimit'
type RawResult = {
  summary: string
  description?: string
  score: number
  source?: string
  assignee?: string
  created?: string
  updated?: string
  url?: string
  color?: string
}

function getScoreColor(score: number) {
  if (score >= 0.85) return "bg-green-600 text-white"
  if (score >= 0.6) return "bg-yellow-500 text-white"
  return "bg-red-500 text-white"
}

export default function RawResultCard({ result }: { result: RawResult }) {
  const [expand, setExpand] = useState(false);
  const charLimit = useCharLimit();


  return (
    <Card className="p-4 space-y-2 result-card">
      <div className="flex justify-between items-center">
        <h3 className="font-semibold text-lg">{result.summary}</h3>
        <Badge className={getScoreColor(result.score)}>
          Score : {result.score.toFixed(2)}
        </Badge>
      </div>

      {result.description && (
        <div className="text-sm text-muted-foreground whitespace-pre-wrap">
          {expand || result.description.length <= charLimit
            ? result.description
            : result.description.slice(0, charLimit) + '...'}
          {result.description.length > charLimit && !expand && (
            <button onClick={() => setExpand(true)} className="text-xs text-blue-600 hover:underline ml-2">
              Afficher plus
            </button>
          )}
        </div>
      )}

      <div className="text-sm text-muted-foreground grid gap-1">
        {result.assignee && <p>👤 Assigné à : <strong>{result.assignee}</strong></p>}
        {result.created && <p>🕒 Créé le : {result.created}</p>}
        {result.updated && <p>🔁 Mis à jour : {result.updated}</p>}
        {result.source && <p>📁 Source : <strong>{result.source}</strong></p>}
      </div>

      {result.url && (
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-blue-600 hover:underline text-sm mt-2"
        >
          Voir plus <ExternalLink className="h-4 w-4 ml-1" />
        </a>
      )}
    </Card>
  );
}