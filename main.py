#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programme client Qdrant pour IT SPIRIT
Ce programme permet d'interroger les collections Qdrant contenant des informations
sur les clients IT SPIRIT et les systèmes ERP (SAP et NetSuite).
"""

import os
import csv
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Range

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

class QdrantSystem:
    """Système de requêtes pour les collections Qdrant d'IT SPIRIT"""
    
    def __init__(self, clients_file: str):
        """
        Initialise le système de requêtes