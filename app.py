#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API FastAPI pour le programme client Qdrant d'IT SPIRIT
Ce programme expose une API REST pour interroger les collections Qdrant
"""

import os
import traceback
from typing import List, Optional, Union, Any   
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from main import QdrantSystem
from dotenv import load_dotenv
load_dotenv()

# Création de l'application FastAPI
app = FastAPI(
    title="IT SPIRIT - API Qdrant",
    description="API pour interroger les collections Qdrant contenant des informations sur les clients IT SPIRIT et les systèmes ERP",
    version="1.0.0"
)

# Configuration CORS pour permettre les requêtes cross-origin
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

class SearchRequest(BaseModel):
    query: str
    client: Optional[str] = None
    erp: Optional[str] = None
    format: Optional[str] = "Summary"
    recentOnly: Optional[bool] = False
    limit: Optional[int] = 10
    raw: Optional[bool] = False
    deepresearch: Optional[bool] = False
class TicketPayload(BaseModel):
    client: str
    source: str
    summary: Optional[str]
    created: Optional[int]
    updated: Optional[int]
    assignee: Optional[str]
    url: Optional[str]
    score: Optional[float]
    color: Optional[str]

class SearchResponse(BaseModel):
    format: str
    content: Any
    sources: str

class SummaryResponse(BaseModel):
    format: str
    content: List[str]
    sources: str
@app.head("/")
async def root_head():
    """Endpoint HEAD pour vérifier que l'API est en ligne sans retour de body."""
    return Response(status_code=200)

@app.get("/")
async def root():
    """Point de terminaison racine pour vérifier que l'API est en ligne"""
    return {"status": "online", "message": "API Qdrant d'IT SPIRIT opérationnelle"}

@app.post("/api/search", response_model=Union[SearchResponse, SummaryResponse])
async def search(request: SearchRequest):
    """Point de terminaison pour effectuer une recherche dans les collections Qdrant"""
    try:
        # Logs pour débogage
        print(f"Requête reçue: {request.query}")
        print(f"Client: {request.client}")
        print(f"ERP: {request.erp}")
        print(f"Format: {request.format}")
        print(f"Recent only: {request.recentOnly}")
        print(f"Limit: {request.limit}")

        # Traitement de la requête
        result = qdrant_system.process_query(
            query=request.query,
            client_name=request.client,
            erp=request.erp,
            recent_only=request.recentOnly,
            limit=request.limit,
            format_type=request.format,
            raw=request.raw
        )

        print(f"Résultat: {result}")

        # Adaptation dynamique du modèle de retour selon le format
        format_type = result.get("format", request.format)
        if result.get("meta", {}).get("mode") == "deepresearch":
            print("🧠 GPT spécialisé utilisé via mode DeepResearch")
            print(f"👉 ERP ciblé : {result['meta'].get('erp')}")

        if format_type == "Summary":
            return SummaryResponse(**result)
        else:
            return SearchResponse(**result)

    except Exception as e:
        print(f"Erreur lors du traitement de la requête: {str(e)}")
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "format": "Error",
                "content": [f"Une erreur s'est produite lors du traitement de votre requête: {str(e)}"],
                "sources": ""
            }
        )
@app.get("/api/clients")
async def get_clients():
    """Retourne la liste des clients depuis ListeClients.csv"""
    try:
        clients = list(qdrant_system.clients.keys())
        return {"clients": sorted(clients)}
    except Exception as e:
        return {"clients": [], "error": str(e)}


@app.get("/api/test")
async def test():
    """
    Endpoint de test pour vérifier que l'API fonctionne correctement.
    """
    return {
        "status": "success",
        "message": "API fonctionnelle",
        "version": "1.1.0",
        "features": [
            "Interprétation flexible des requêtes",
            "Détection des clients et ERP",
            "Formatage des dates en jj/mm/aa",
            "Priorisation intelligente des collections"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    # Démarrage du serveur avec Uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
