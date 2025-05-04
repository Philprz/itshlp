'use client'
import { useEffect, useState } from 'react'
import Image from 'next/image'
import { Search, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import GptResultCard from '@/components/GptResultCard'
import DetailResultCard from '@/components/DetailResultCard'
import MetaBadge from '@/components/MetaBadge'
import LoaderMessage from '@/components/LoaderMessage'
import SummaryCard from '@/components/SummaryCard'

function SearchFilters({ client, setClient, clients, erp, setErp, format, setFormat, recentOnly, setRecentOnly, limit, setLimit, setQuery, setResults, setSources, setMeta }) {
  return (
    <div className="filter-grid grid grid-cols-1 sm:grid-cols-3 gap-4">
      <div>
        <Label htmlFor="client" className="text-sm font-medium">Client</Label>
        <Select value={client || 'none'} onValueChange={(v) => setClient(v === 'none' ? '' : v)}>
          <SelectTrigger className="w-full mt-1">
            <SelectValue placeholder="Sélectionner un client..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Aucun</SelectItem>
            {clients.map((c) => (
              <SelectItem key={c} value={c}>{c}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="erp" className="text-sm font-medium">ERP</Label>
        <Select value={erp || 'none'} onValueChange={(v) => setErp(v === 'none' ? '' : v)}>
          <SelectTrigger className="w-full mt-1">
            <SelectValue placeholder="ERP utilisé..." />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="none">Aucun</SelectItem>
            <SelectItem value="SAP">SAP</SelectItem>
            <SelectItem value="NetSuite">NetSuite</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="format" className="text-sm font-medium">Format de réponse</Label>
        <Select value={format} onValueChange={setFormat}>
          <SelectTrigger className="w-full mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="Summary">Résumé</SelectItem>
            <SelectItem value="Detail">Détail</SelectItem>
            <SelectItem value="Guide">Guide</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div>
        <Label htmlFor="limit" className="text-sm font-medium">Nombre de résultats</Label>
        <Select value={limit} onValueChange={setLimit}>
          <SelectTrigger className="w-full mt-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="3">3</SelectItem>
            <SelectItem value="5">5</SelectItem>
            <SelectItem value="10">10</SelectItem>
            <SelectItem value="20">20</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="col-span-1 sm:col-span-3 flex items-center space-x-2 mt-2">
        <Checkbox id="recentOnly" checked={recentOnly} onCheckedChange={(checked) => setRecentOnly(!!checked)} />
        <Label htmlFor="recentOnly" className="text-sm font-medium">
          Afficher uniquement les tickets récents (moins de 6 mois)
        </Label>
      </div>

      <div className="col-span-1 sm:col-span-3 mt-4">
        <Button
          variant="secondary"
          className="w-full"
          onClick={() => {
            setClient('')
            setErp('')
            setFormat('Summary')
            setRecentOnly(true)
            setLimit('5')
            setQuery('')
            setResults([]);
            setSources('');
            setMeta(null);
          }}
        >
          🔄 Réinitialiser les filtres
        </Button>
      </div>
    </div>
  );
}

export default function Home() {
  const [query, setQuery] = useState('')
  const [client, setClient] = useState('')
  const [clients, setClients] = useState<string[]>([])
  const [erp, setErp] = useState('')
  const [format, setFormat] = useState('Summary')
  const [recentOnly, setRecentOnly] = useState(true)
  const [limit, setLimit] = useState('5')
  const [results, setResults] = useState<any[]>([])
  const [sources, setSources] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [meta, setMeta] = useState<any>(null)
  const [showFilters, setShowFilters] = useState(false)
  useEffect(() => {
    if (meta?.partial) {
      const interval = setInterval(async () => {
        const response = await fetch('/api/search', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query, client, erp, format, recentOnly, limit: parseInt(limit) }),
        });
  
        const data = await response.json();
        const isStillPartial = data.meta?.partial;
  
        // Dès qu'on a une version enrichie, on met à jour
        if (!isStillPartial) {
          setResults(Array.isArray(data.content) ? data.content : [data.content]);
          setSources(data.sources || '');
          setMeta(data.meta || null);
          clearInterval(interval);
          console.log("✅ Version enrichie récupérée automatiquement.");
        }
      }, 5000); // toutes les 5 sec
  
      return () => clearInterval(interval); // nettoyage
    }
  }, [meta]);
  
  useEffect(() => {
    const fetchClients = async () => {
      try {
        const res = await fetch('/api/clients')
        const data = await res.json()
        if (Array.isArray(data.clients)) {
          const sorted = data.clients.filter(Boolean).sort((a, b) => a.localeCompare(b))
          setClients(sorted)
        }
      } catch (err) {
        console.error('Erreur chargement clients', err)
      }
    }
    fetchClients()
  }, [])

  const handleSearch = async () => {
    if (!query) {
      setError('Veuillez entrer une requête de recherche');
      return;
    }
    // 💡 Reset des anciens résultats avant le chargement
    setResults([]);        // Supprime les résultats précédents
    setSources('');        // Supprime les sources
    setMeta(null);         // Supprime les métadonnées
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query, client, erp, format, recentOnly, limit: parseInt(limit) }),
      });

      const data = await response.json();
      const content = data.content;
      const isPartial = data.meta?.partial;

      setResults(Array.isArray(content) ? content : [content]);
      setSources(data.sources || '');
      setMeta(data.meta || null);
    } catch (err: any) {
      setError(err.message);
      setResults([]);
      setQuery('');
      setSources('');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex min-h-screen flex-col">
      <header className="bg-white dark:bg-gray-900 shadow-sm py-4 px-6 flex items-center justify-between rounded-b-lg border-b">
        <div className="flex items-center space-x-4">
          <Image src="/it_spirit_logo.jfif" alt="Logo ITSpirit" width={64} height={64} className="rounded-md" priority />
          <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white">ITS Help</h1>
        </div>
      </header>

      <div className="p-4 sm:p-8">
        <Card className="search-form p-6 mb-8">
          <Label htmlFor="query" className="text-lg font-medium">Requête</Label>
          <div className="flex gap-2 mt-1">
            <Input id="query" placeholder="Entrez votre requête..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearch()} className="text-base" />
            <Button onClick={handleSearch} disabled={isLoading} className="search-button">
              {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />} Rechercher
            </Button>
          </div>

          <Button variant="outline" onClick={() => setShowFilters(!showFilters)} className="mt-4">
            {showFilters ? 'Masquer les filtres' : 'Filtres avancés'}
          </Button>

          {showFilters && (
            <SearchFilters
              client={client} setClient={setClient} clients={clients}
              erp={erp} setErp={setErp}
              format={format} setFormat={setFormat}
              recentOnly={recentOnly} setRecentOnly={setRecentOnly}
              limit={limit} setLimit={setLimit}
              setQuery={setQuery}
              setResults={setResults}
              setSources={setSources}
              setMeta={setMeta}
            />
          )}
        </Card>

        {isLoading && <Card className="mb-8"><LoaderMessage /></Card>}
        {error && <Card className="error-message p-4 mb-8"><p>{error}</p></Card>}

        {!isLoading && results.length > 0 && (
          <Card className="results-section p-4">
            <div className="results-header">
              <h2 className="results-count">Résultats ({results.length})</h2>
              {sources && <p className="results-sources">Sources: {sources}</p>}
            </div>

            {recentOnly && (
              <p className="text-sm text-green-700 dark:text-green-300 italic mb-2">
                ✅ Filtrage activé : tickets créés il y a moins de 6 mois
              </p>
            )}

            <p className="text-sm text-gray-700 dark:text-gray-300 italic mb-2">
              🛠️ Format sélectionné : <strong>
                {format === 'Summary' ? 'Résumé global' : format === 'Detail' ? 'Affichage détaillé' : 'Guide pratique'}
              </strong>
            </p>

            {meta && <MetaBadge meta={meta} />}

            <ScrollArea className="h-[400px]">
              {meta?.partial && results.map((r, i) => <GptResultCard key={i} content={r} />)}
              {!meta?.partial && format === 'Summary' && results.map((r, i) => <SummaryCard key={i} content={r} format={format} isGpt={meta?.mode === 'deepresearch'} />)}
              {!meta?.partial && format === 'Detail' && results.map((r, i) => <DetailResultCard key={i} result={r} />)}
              {!meta?.partial && format === 'Guide' && results.map((r, i) => <GptResultCard key={i} content={r} />)}
            </ScrollArea>

            <div className="question-client-block mt-4 space-y-2">
              <p className="text-sm font-medium">Est-ce que votre question porte sur un client en particulier ?</p>
              <Select value={client || 'none'} onValueChange={(v) => setClient(v === 'none' ? '' : v)}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Sélectionner un client" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Aucun</SelectItem>
                  {clients.map((c) => (
                    <SelectItem key={c} value={c}>{c}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button variant="secondary" size="sm" onClick={handleSearch}>🔁 Relancer avec ce client</Button>
            </div>
          </Card>
        )}
      </div>
    </main>
  );
}
