// PATCH Étendu : DetailResultCard.tsx avec seuil dynamique responsive

'use client'

import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import Link from 'next/link'
import { useEffect, useState } from 'react'
import { ChevronDown } from 'lucide-react'
import useCharLimit from '@/hooks/useCharLimit'
const getScoreColor = (color: string) => {
  switch (color) {
    case 'green': return 'bg-green-600 text-white';
    case 'orange': return 'bg-yellow-500 text-white';
    case 'red': return 'bg-red-600 text-white';
    default: return 'bg-gray-400 text-white';
  }
}

const getSourceIcon = (source: string) => {
  const icons: Record<string, string> = {
    jira: '🟦',
    zendesk: '🟩',
    email: '✉️',
    github: '🐙',
    servicenow: '🟧',
  };
  return icons[source?.toLowerCase()] || '📄';
}

export default function DetailResultCard({ result }: { result: any }) {
  if (!result) return null;

  const {
    client,
    erp,
    created,
    updated,
    summary,
    description,
    comments,
    source_type,
    key,
    assignee,
    company_name,
    url,
    page_url,
    content,
    score,
    color
  } = result;

  const externalLink = url || page_url;
  const [expandDescription, setExpandDescription] = useState(false);
  const [expandContent, setExpandContent] = useState(false);
  const charLimit = useCharLimit();


  return (
    <Card className="result-card-enhanced p-6 space-y-4 animate-fade-in">
      <div className="flex justify-between items-start">
        <div className="space-y-1">
          <div className="flex justify-between items-center mb-1">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">
              {summary || key || 'Ticket'}
            </h3>
            {score !== undefined && (
              <Badge className={getScoreColor(color)}>🎯 {score}</Badge>
            )}
          </div>

          <div className="flex flex-wrap gap-2 text-sm">
            {assignee && <Badge className="bg-teal-100 text-teal-800 border border-teal-300">👤 {assignee}</Badge>}
            {(client || company_name) && <Badge className="bg-gray-100 text-gray-700 border border-gray-300">🏢 {client || company_name}</Badge>}
            {erp && <Badge className="bg-indigo-100 text-indigo-800 border border-indigo-300">🏷️ ERP : {erp}</Badge>}
          </div>

          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            📅 {created || '—'} — 🔄 {updated || '—'}
          </p>
        </div>

        {externalLink && (
          <div className="flex flex-col items-end gap-1">
            <Link href={externalLink} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline text-sm">
              🔗 Voir dans {source_type || 'source'}
            </Link>
            <button onClick={() => navigator.clipboard.writeText(externalLink)} className="text-xs text-blue-500 hover:underline">
              📋 Copier le lien
            </button>
          </div>
        )}
      </div>

      {description && (
        <div className="space-y-1">
          <p className="font-medium text-sm">📌 Description</p>
          <div className={`text-sm whitespace-pre-wrap text-gray-700 dark:text-gray-200 ${expandDescription ? '' : 'line-clamp-5'}`}>
            {description}
          </div>
          {description.length > charLimit && !expandDescription && (
            <button onClick={() => setExpandDescription(true)} className="text-xs text-blue-600 hover:underline flex items-center">
              Afficher plus <ChevronDown className="h-3 w-3 ml-1" />
            </button>
          )}
        </div>
      )}

      {content && (
        <div className="space-y-1">
          <p className="font-medium text-sm">📄 Contenu</p>
          <div className={`text-sm italic text-gray-700 dark:text-gray-300 whitespace-pre-wrap ${expandContent ? '' : 'line-clamp-5'}`}>
            {content}
          </div>
          {content.length > charLimit && !expandContent && (
            <button onClick={() => setExpandContent(true)} className="text-xs text-blue-600 hover:underline flex items-center">
              Afficher plus <ChevronDown className="h-3 w-3 ml-1" />
            </button>
          )}
        </div>
      )}

      {comments && (
        <blockquote className="text-sm text-gray-500 italic border-l-4 pl-4 border-gray-300">
          💬 {comments}
        </blockquote>
      )}

      <div className="flex justify-between items-center text-sm pt-2 border-t mt-4">
        <p className="text-gray-700 dark:text-gray-200">
          📁 Source : <strong>{getSourceIcon(source_type)} {source_type || '—'}</strong>
        </p>
      </div>
    </Card>
  );
}
