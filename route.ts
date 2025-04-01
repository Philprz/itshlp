}

// Gestionnaire de la route API
export async function POST(request: NextRequest) {
  try {
    const { query, client, erp, format, recentOnly, limit } = await request.json();
    
    // Vérification des paramètres requis
    if (!query) {
      return NextResponse.json(
        { error: 'Le paramètre query est requis' },
        { status: 400 }
      );
    }
    
    // Vérification si la requête est ambiguë
    if (isQueryAmbiguous(query, client, erp)) {
      return NextResponse.json({
        format: "Clarification",
        content: ["Votre requête est ambiguë. Pourriez-vous préciser pour quel ERP (SAP ou NetSuite) vous souhaitez des informations ?"],
        sources: ""
      });
    }
    
    // Récupération des collections prioritaires
    const prioritizedCollections = getPrioritizedCollections(client, erp);
    
    // Recherche dans chaque collection
    const allResults = [];
    const collectionsUsed = [];
    
    for (const collectionName of prioritizedCollections) {
      const results = await searchInCollection(
        collectionName,
        query,
        client,
        recentOnly,
        limit
      );
      
      if (results.length > 0) {
        allResults.push(...results);
        collectionsUsed.push(collectionName);
        
        // Si on a suffisamment de résultats, on s'arrête
        if (allResults.length >= limit) {
          break;
        }
      }
    }
    
    // Formatage des résultats
    const formattedResults = allResults
      .slice(0, limit)
      .map(result => formatResponse(result, format));
    
    // Création de la réponse finale
    return NextResponse.json({
      format,
      content: formattedResults,
      sources: collectionsUsed.join(", ")
    });
  } catch (error: any) {
    console.error('Erreur lors du traitement de la requête:', error);
    return NextResponse.json(
      { error: error.message || 'Une erreur est survenue lors du traitement de la requête' },
      { status: 500 }
    );
  }