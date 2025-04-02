#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API FastAPI pour le programme client Qdrant d'IT SPIRIT
Ce programme expose une API REST pour interroger les collections Qdrant
"""

import os
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import QdrantSystem

# Création de l'application FastAPI
app = FastAPI(
    title="IT SPIRIT - API Qdrant",
    description="API pour interroger les collections Qdrant contenant des informations sur les clients IT SPIRIT et les systèmes ERP",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes depuis le frontend Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier l'origine exacte du frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialisation du système Qdrant
clients_file = "ListeClients.csv"
qdrant_system = QdrantSystem(clients_file)

# Modèle de données pour la requête
class QueryRequest(BaseModel):
    query: str
    client: Optional[str] = None
    erp: Optional[str] = None
    format: str = "Summary"
    recentOnly: bool = True
    limit: int = 5

# Modèle de données pour la réponse
class QueryResponse(BaseModel):
    format: str
    content: List[str]
    sources: str

@app.get("/")
async def root():
    """Point de terminaison racine pour vérifier que l'API est en ligne"""
    return {"status": "online", "message": "API Qdrant d'IT SPIRIT opérationnelle"}

@app.post("/api/search", response_model=QueryResponse)
async def search(request: QueryRequest):
    """Point de terminaison pour effectuer une recherche dans les collections Qdrant"""
    try:
        # Vérification des paramètres requis
        if not request.query:
            raise HTTPException(status_code=400, detail="Le paramètre query est requis")
        
        # Vérification si la requête est ambiguë
        if qdrant_system.is_query_ambiguous(request.query, request.client, request.erp):
            return {
                "format": "Clarification",
                "content": ["Votre requête est ambiguë. Pourriez-vous préciser pour quel ERP (SAP ou NetSuite) vous souhaitez des informations ?"],
                "sources": ""
            }
        
        # Traitement de la requête
        result = qdrant_system.process_query(
            query_text=request.query,
            client_name=request.client,
            erp=request.erp,
            recent_only=request.recentOnly,
            limit=request.limit,
            format_type=request.format
        )
        
        # Extraction des résultats et des sources
        content = result.get("content", [])
        sources = result.get("sources", "")
        
        return {
            "format": request.format,
            "content": content,
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Démarrage du serveur avec Uvicorn
    # host="0.0.0.0" permet d'accéder au serveur depuis l'extérieur
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
