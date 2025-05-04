// app/error.tsx
'use client'

import { useEffect } from 'react'

export default function Error({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error('Erreur capturée par ErrorBoundary :', error)
  }, [error])

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4 text-red-600">Une erreur est survenue</h2>
      <p className="mb-4">{error.message || "Erreur inconnue."}</p>
      <button
        onClick={() => reset()}
        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
      >
        Réessayer
      </button>
    </div>
  )
}
