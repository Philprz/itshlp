#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script complémentaire pour tester spécifiquement le contenu des collections Qdrant avec des requêtes d'embedding précises et des filtres basés sur les payloads.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Gestion des dépendances avec messages explicites
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue
except ModuleNotFoundError:
    print("❌ Erreur : le module 'qdrant-client' n'est pas installé. Installe-le avec :")
    print("pip install qdrant-client")
    exit(1)

# Chargement des variables d'environnement
load_dotenv()

# Configuration des clients
qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Définition des collections
collections_payloads = {
    "ZENDESK": ["client", "erp", "summary"],
    "JIRA": ["client", "erp", "summary"],
    "CONFLUENCE": ["client", "erp", "summary"],
    "SAP": ["title", "text"],
    "NETSUITE": ["title", "content"],
    "NETSUITE_DUMMIES": ["title", "text"]
}

# Test des requêtes pour chaque collection
def test_collection_query(collection_name, query, client_name=None, limit=3):
    print(f"\n🔍 Collection : {collection_name}")
    print(f"📝 Requête : '{query}' (Client : {client_name if client_name else 'Aucun'})")

    # Génération d'embedding
    embedding_response = openai_client.embeddings.create(
        input=query,
        model="text-embedding-ada-002"
    )
    query_vector = embedding_response.data[0].embedding

    # Construction du filtre
    filters = []
    if client_name and "client" in collections_payloads[collection_name]:
        filters.append(FieldCondition(key="client", match=MatchValue(value=client_name)))

    query_filter = Filter(must=filters) if filters else None

    # Recherche Qdrant
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=limit
    )

    # Affichage des résultats
    if results:
        print(f"✅ {len(results)} résultats trouvés :")
        for i, result in enumerate(results, 1):
            payload = result.payload
            print(f"\n📌 Résultat {i} (score : {result.score:.4f})")
            for key in collections_payloads[collection_name]:
                print(f"   - {key.capitalize()} : {payload.get(key, 'Non disponible')}")
    else:
        print("⚠️ Aucun résultat trouvé.")

# Exemples de tests
if __name__ == "__main__":
    test_collection_query("JIRA", "problème connexion", "AZERGO")
    test_collection_query("CONFLUENCE", "documentation ERP")
    test_collection_query("ZENDESK", "ticket incident", "AZERGO")
    test_collection_query("SAP", "module finance")
    test_collection_query("NETSUITE", "gestion stocks")
    test_collection_query("NETSUITE_DUMMIES", "comptabilité analytique")
