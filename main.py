#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programme client Qdrant pour IT SPIRIT
Ce programme permet d'interroger les collections Qdrant contenant des informations
sur les clients IT SPIRIT et les systèmes ERP (SAP et NetSuite).
"""

import os
from dotenv import load_dotenv
from query_system import QdrantSystem

# Chargement des variables d'environnement
load_dotenv()

# Configuration Qdrant
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_ZENDESK = os.getenv("QDRANT_COLLECTION_ZENDESK", "ZENDESK")
QDRANT_COLLECTION_JIRA = os.getenv("QDRANT_COLLECTION_JIRA", "JIRA")
QDRANT_COLLECTION_CONFLUENCE = os.getenv("QDRANT_COLLECTION_CONFLUENCE", "CONFLUENCE")
QDRANT_COLLECTION_NETSUITE = os.getenv("QDRANT_COLLECTION_NETSUITE", "NETSUITE")
QDRANT_COLLECTION_NETSUITE_DUMMIES = os.getenv("QDRANT_COLLECTION_NETSUITE_DUMMIES", "NETSUITE_DUMMIES")
QDRANT_COLLECTION_SAP = os.getenv("QDRANT_COLLECTION_SAP", "SAP")

# Définition des collections
COLLECTIONS = {
    "ZENDESK": QDRANT_COLLECTION_ZENDESK,
    "JIRA": QDRANT_COLLECTION_JIRA,
    "CONFLUENCE": QDRANT_COLLECTION_CONFLUENCE,
    "NETSUITE": QDRANT_COLLECTION_NETSUITE,
    "NETSUITE_DUMMIES": QDRANT_COLLECTION_NETSUITE_DUMMIES,
    "SAP": QDRANT_COLLECTION_SAP
}

# Définition des formats de réponse
FORMATS = ["Summary", "Detail", "Guide"]

def search_all_clients(query_text: str, format_type="Summary", recent_only=False, limit=3):
    """
    Exécute une requête pour tous les clients du fichier ListeClients.csv
    """
    clients_file = "ListeClients.csv"
    system = QdrantSystem(clients_file)
    all_results = {}

    for client_name in system.clients:
        try:
            result = system.process_query(
                query=query_text,
                client_name=client_name,
                format_type=format_type,
                recent_only=recent_only,
                limit=limit
            )
            all_results[client_name] = result["content"]
        except Exception as e:
            all_results[client_name] = [f"Erreur: {str(e)}"]

    return all_results


if __name__ == "__main__":
    results = search_all_clients("Problèmes de connexion", format_type="Summary", recent_only=False)

    # Affichage des résultats
    for client, responses in results.items():
        print(f"\n=== {client} ===")
        for r in responses:
            print(f"- {r}")
