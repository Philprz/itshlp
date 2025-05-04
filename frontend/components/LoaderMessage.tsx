'use client'

import { Loader2 } from 'lucide-react'

export default function LoaderMessage() {
  return (
    <div className="flex flex-col items-center justify-center text-center py-10 text-gray-700 dark:text-gray-300 animate-pulse">
      <Loader2 className="h-8 w-8 animate-spin mb-3 text-blue-600" />
      <p className="text-lg font-medium">⏳ Analyse en cours...</p>
      <p className="text-sm text-muted-foreground">Merci de patienter pendant l’analyse de la requête.</p>
    </div>
  );
}
