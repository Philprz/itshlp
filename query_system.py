#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de requêtes pour les collections Qdrant d'IT SPIRIT
Ce système permet d'interroger les collections Qdrant selon les priorités définies
et de formater les réponses selon les formats demandés.
"""

import csv
import os
import re   
import json
import openai
import unicodedata
from fuzzywuzzy import fuzz 
from datetime import datetime, timedelta
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client.http.models import FieldCondition, MatchValue, Range, Filter
from qdrant_client import QdrantClient
from time import time
from cache_manager import CacheManager

# Chargement des variables d'environnement
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Définition du prompt système pour OpenAI
system_prompt = """
Tu es un assistant expert dans l’analyse de requêtes utilisateur pour le moteur de recherche IT SPIRIT. Ton rôle est de transformer ces requêtes en instructions structurées, selon les règles suivantes :

### Règles de sélection des collections :
1. Si la requête contient les mots "ticket" ou "incident" :
   → Utiliser les collections : JIRA, CONFLUENCE, ZENDESK

2. Si la requête mentionne "NetSuite" ou fait référence à cet ERP :
   → Utiliser : NETSUITE, NETSUITE_DUMMIES
   → Ajouter : JIRA, CONFLUENCE, ZENDESK avec un filtre `erp = "NetSuite"`
   → Si un client est précisé, inclure les collections associées à ce client

3. Si la requête mentionne "SAP" ou concerne cet ERP :
   → Utiliser : SAP (et potentiellement JIRA, CONFLUENCE, ZENDESK)
   → Si un client est précisé, inclure les collections associées à ce client

4. Si la requête mentionne explicitement une collection :
   - "ZENDESK" ou "Zendesk" → Ajouter ZENDESK
   - "CONFLUENCE" ou "Confluence" → Ajouter CONFLUENCE
   - "JIRA" ou "Jira" → Ajouter JIRA
   → Si un client est précisé, inclure les collections associées

### Format de sortie :
Tu dois retourner un JSON brut, sans balises Markdown ni code. Ce JSON doit contenir :
- `collections`: Liste des collections à interroger (parmi : JIRA, CONFLUENCE, ZENDESK, NETSUITE, NETSUITE_DUMMIES, SAP)
- `filters`: Dictionnaire de filtres (par ex. `client`, `erp`, `date`, etc.)
- `use_embedding`: Booléen indiquant si la recherche utilise l’embedding
- `limit`: Nombre de résultats à retourner

### Consignes spécifiques :
- Si la requête concerne des sujets génériques liés à un ERP (ex : "configurer un module NetSuite"), ajoute un filtre `erp` avec "NetSuite" ou "SAP"
- Si la requête contient des termes vagues comme "tickets récents", ajoute un filtre de date au format : `{"date": {"gte": <timestamp il y a 6 mois>}}`
"""

# Définition des collections
COLLECTIONS = ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES", "SAP"]

# Définition des formats de réponse
FORMATS = ["Summary", "Detail", "Guide"]

def normalize_string(text: str) -> str:
    if not text:
        return ""
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    return text.upper().strip()

def extract_client_name_from_csv(query: str, csv_path: str = "ListeClients.csv"):
    """
    Détecte un nom de client dans une requête utilisateur, basé sur ListeClients.csv
    Retourne: (nom_client, score, source)
    """
    if not query or len(query.strip()) < 2:
        return None, 0.0, {}

    query_normalized = normalize_string(query)
    best_match = None
    best_score = 0
    best_source = None

    try:
        with open(csv_path, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                client_name = row.get("Client", "").strip()
                if not client_name:
                    continue

                # Match exact
                if normalize_string(client_name) in query_normalized:
                    return client_name, 100.0, {"source": client_name}

                # Match flou
                score = fuzz.ratio(query_normalized, normalize_string(client_name))
                if score > best_score:
                    best_score = score
                    best_match = client_name
                    best_source = client_name

        if best_match and best_score >= 80:
            return best_match, best_score, {"source": best_source}

    except Exception as e:
        print(f"[⚠️] Erreur lors de la détection client depuis CSV: {e}")

    return None, 0.0, {}

def extract_json(text: str) -> str:
    match = re.search(r"\{[\s\S]*\}", text)
    return match.group(0) if match else text
def call_openai_assistant(erp: str, query: str) -> str:
    assistant_id = None
    if erp and "netsuite" in erp.lower():
        assistant_id = os.getenv("ASSISTANT_ID_NETSUITE")
    elif erp and "sap" in erp.lower():
        assistant_id = os.getenv("ASSISTANT_ID_SAP")


    if not assistant_id:
        return "⚠️ Aucun assistant configuré pour cet ERP."

    try:
        thread = openai.beta.threads.create()
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )

        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        while True:
            status = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if status.status == "completed":
                break
            elif status.status in ["failed", "cancelled"]:
                return f"❌ Assistant {erp} : échec ({status.status})"
            time.sleep(1)

        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value
        openai.beta.threads.delete(thread_id=thread.id)
        return response

    except Exception as e:
        return f"❌ Erreur assistant {erp} : {str(e)}"
class QdrantSystem:
    """Système de requêtes pour les collections Qdrant d'IT SPIRIT"""
    
    def __init__(self, clients_file: str):
        """
        Initialise le système de requêtes
        
        Args:
            clients_file: Chemin vers le fichier CSV contenant les informations clients
        """
        self.clients = self._load_clients(clients_file)
        self.collections = COLLECTIONS
        self.formats = FORMATS
        self.client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.cache = CacheManager(
            db_url=os.getenv("DATABASE_URL"),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0")
        )
        print("[🔧] REDIS_URL chargé :", os.getenv("REDIS_URL"))

    def enrich_query_with_openai(self, user_query):
        """
        Enrichit une requête utilisateur en utilisant l'API OpenAI et en ajoutant des filtres locaux.

        Args:
            user_query (str): La requête utilisateur à enrichir.

        Returns:
            dict: La requête enrichie sous forme de dictionnaire JSON.
        """
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.0,
            max_tokens=500
        )

        enriched_query = response.choices[0].message.content.strip()
        enriched_json = json.loads(extract_json(enriched_query))

        filters = enriched_json.get("filters", {})
        # 🔁 Si client détecté mais pas d'ERP, on complète avec l'ERP du client
        if not filters.get("erp") and filters.get("client"):
            client_erp = self.get_client_erp(filters["client"])
            if client_erp:
                filters["erp"] = client_erp
                enriched_json["filters"] = filters

        query_upper = user_query.upper()

        if "date" not in filters and any(w in query_upper for w in ["TICKET", "RÉCENT", "RÉCENTS", "RECENT"]):
            # Filtre date arrondi au début du mois, stable
            six_months_ago_date = (datetime.now() - timedelta(days=180)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filters["date"] = {"gte": int(six_months_ago_date.timestamp())}
            enriched_json["filters"] = filters

        if not filters.get("client"):
            detected_client, score, _ = extract_client_name_from_csv(user_query)
            if detected_client:
                filters["client"] = detected_client
                enriched_json["filters"] = filters

        print("[🧠 GPT - Query enrichie]", json.dumps(enriched_json, indent=2))
        return enriched_json
    
    def _load_clients(self, clients_file: str) -> Dict[str, Dict[str, Any]]:
        """
        Charge les informations clients depuis le fichier CSV
        
        Args:
            clients_file: Chemin vers le fichier CSV contenant les informations clients
            
        Returns:
            Dictionnaire des clients avec leurs informations
        """
        clients = {}
        
        with open(clients_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                client_name = row['Client']
                if client_name not in clients:
                    clients[client_name] = {
                        'consultant': row['Consultant'],
                        'statut': row['Statut'],
                        'jira': row['JIRA'],
                        'zendesk': row['ZENDESK'],
                        'confluence': row['CONFLUENCE'],
                        'erp': row['ERP']
                    }
                # Si le client existe déjà, on ne met à jour que les champs vides
                else:
                    for field, csv_field in [('consultant', 'Consultant'), ('statut', 'Statut'), 
                                           ('jira', 'JIRA'), ('zendesk', 'ZENDESK'), 
                                           ('confluence', 'CONFLUENCE'), ('erp', 'ERP')]:
                        if not clients[client_name][field] and row[csv_field]:
                            clients[client_name][field] = row[csv_field]
        
        return clients
    def simple_filter_search(self, collection_name, client_name=None, recent_only=False, filters: Filter = None, limit=5):
        """
        Effectue une recherche simple dans une collection Qdrant sans vectorisation.

        Args:
            collection_name: Nom de la collection Qdrant
            client_name: Nom du client pour le filtrage (optionnel)
            recent_only: Si True, filtre les résultats pour les éléments créés il y a moins de 6 mois (optionnel)
            filters: Objet Filter Qdrant à appliquer (filtrage par client, date, etc.) (optionnel)
            limit: Nombre de résultats à retourner

        Returns:
            Liste des payloads formatés
        """
        filter_conditions = []

        if client_name:
            filter_conditions.append(
                FieldCondition(
                    key="client",
                    match=MatchValue(value=client_name)
                )
            )

        if recent_only:
            # Filtre date arrondi au début du mois, stable
            six_months_ago_date = (datetime.now() - timedelta(days=180)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            filter_conditions.append(
                FieldCondition(
                    key="created",
                    range=Range(gte=int(six_months_ago_date.timestamp()))
                )
            )

        if filters:
            search_filter = filters
        else:
            search_filter = Filter(must=filter_conditions) if filter_conditions else None

        results, _ = self.client.scroll(
            collection_name=collection_name,
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True
        )

        return [self.format_ticket_payload(hit.payload) for hit in results]

    def search_in_collection(self, collection_name: str, query: str, client_name: str = None, recent_only: bool = False, limit: int = 5, filters: Filter = None):
        """
        Effectue une recherche dans une collection avec vectorisation et filtres.

        Args:
            collection_name: Nom de la collection
            query: Texte de la requête utilisateur
            client_name: Nom du client (optionnel, redondant avec filters)
            recent_only: Booléen pour filtrer les données récentes (non utilisé ici)
            limit: Nombre de résultats à retourner
            filters: Filtre Qdrant (déjà construit via enrich_query_with_openai)

        Returns:
            Liste des documents pertinents (payloads) avec leurs scores
        """
        embedding_response = openai_client.embeddings.create(
            input=query,
            model="text-embedding-ada-002"
        )
        query_vector = embedding_response.data[0].embedding

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=filters,
            limit=limit,
            with_payload=True
        )

        return [(hit.payload, hit.score) for hit in results]

    def get_client_erp(self, client_name: str) -> str:
        """
        Récupère le système ERP utilisé par un client
        
        Args:
            client_name: Nom du client
            
        Returns:
            Système ERP utilisé par le client (SAP ou NetSuite)
        """
        if client_name in self.clients:
            return self.clients[client_name]['erp']
        return ""
    
    def get_client_info(self, client_name: str) -> Dict[str, Any]:
        """
        Récupère les informations d'un client
        
        Args:
            client_name: Nom du client
            
        Returns:
            Informations du client
        """
        if client_name in self.clients:
            return self.clients[client_name]
        return {}
    
    def get_prioritized_collections(self, client_name: str = "", erp: str = "") -> List[str]:
        """
        Récupère les collections prioritaires selon le client et le système ERP
        
        Args:
            client_name: Nom du client (optionnel)
            erp: Système ERP (optionnel)
            
        Returns:
            Liste des collections prioritaires
        """
        # Si on a un client, on priorise JIRA, CONFLUENCE, ZENDESK
        if client_name:
            if erp == "SAP":
                return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
            elif erp == "NetSuite":
                return ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES"]
            else:
                # Si on ne connaît pas l'ERP, on vérifie dans les données client
                client_erp = self.get_client_erp(client_name)
                if client_erp == "SAP":
                    return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
                elif client_erp == "NetSuite":
                    return ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES"]
                else:
                    # Si on ne trouve toujours pas l'ERP, on renvoie toutes les collections
                    return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Si on a un ERP mais pas de client
        if erp == "SAP":
            return ["SAP", "JIRA", "CONFLUENCE", "ZENDESK"]
        elif erp == "NetSuite":
            return ["NETSUITE", "NETSUITE_DUMMIES", "JIRA", "CONFLUENCE", "ZENDESK"]
        
        # Si on n'a ni client ni ERP, on renvoie toutes les collections
        return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
    
    def is_recent(self, date_str: str) -> bool:
        """
        Vérifie si une date est récente (moins de 6 mois)
        
        Args:
            date_str: Date au format string
            
        Returns:
            True si la date est récente, False sinon
        """
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
            six_months_ago = datetime.now() - timedelta(days=180)
            return date >= six_months_ago
        except (ValueError, TypeError):
            return False

    def format_ticket_payload(self, payload: dict, score: float = None, format_type: str = "Detail") -> dict:
        def get_score_color(score):
            if score is None:
                return "gray"
            if score >= 0.80:
                return "green"
            elif score >= 0.50:
                return "orange"
            else:
                return "red"

        def format_timestamp(ts):
            try:
                if isinstance(ts, (int, float)):
                    return datetime.fromtimestamp(ts).strftime('%d/%m/%Y')
                elif isinstance(ts, str) and ts.isdigit():
                    return datetime.fromtimestamp(int(ts)).strftime('%d/%m/%Y')
                return ts
            except Exception:
                return ts

        base = {
            "client": payload.get("client", "N/A"),
            "erp": payload.get("erp", "N/A"),
            "summary": payload.get("summary", payload.get("description", "")),
            "description": payload.get("description", ""),
            "content": payload.get("content", ""),
            "comments": payload.get("comments", ""),
            "created": format_timestamp(payload.get("created", "N/A")),
            "updated": format_timestamp(payload.get("updated", "N/A")),
            "assignee": payload.get("assignee", "N/A"),
            "source": payload.get("source_type", "N/A"),
            "key": payload.get("key", None),
            "url": payload.get("url") or payload.get("page_url"),
            "company_name": payload.get("company_name", None),
            "score": round(score, 4) if score is not None else None,
            "color": get_score_color(score),
        }

        if format_type == "Guide":
            content_parts = []
            for key in ["summary", "description", "content", "text", "comments"]:
                val = payload.get(key)
                if val:
                    content_parts.append(str(val))
            base["content"] = "\n".join(content_parts)

        return base

    def format_response(self, content: Dict[str, Any], format_type: str = "Summary") -> str:
        """
        Formate la réponse selon le format demandé
        
        Args:
            content: Contenu de la réponse
            format_type: Format de la réponse (Summary, Detail, Guide)
            
        Returns:
            Réponse formatée
        """
        if format_type not in self.formats:
            format_type = "Summary"
        
        # Formatage selon le type demandé
        if format_type == "Summary":
            # Résumé bref
            return self._format_summary(content)
        elif format_type == "Detail":
            # Explication complète
            return self._format_detail(content)
        elif format_type == "Guide":
            # Instructions étape par étape
            return self._format_guide(content)
    @staticmethod
    def convert_to_timestamp(date_str):
        if isinstance(date_str, (int, float)):
            return date_str
        try:
            return int(datetime.fromisoformat(date_str.replace("Z", "+00:00")).timestamp())
        except Exception:
            return None  # ou raise une erreur selon ton choix

    def apply_filters(self, filters: dict) -> Filter:
        """
        Transforme un dictionnaire de filtres en objet Filter pour Qdrant

        Args:
            filters: Dictionnaire de filtres (client, erp, date, etc.)

        Returns:
            Objet Filter compatible avec Qdrant
        """
        conditions = []

        if "client" in filters:
            conditions.append(
                FieldCondition(key="client", match=MatchValue(value=filters["client"]))
            )

        if "erp" in filters:
            conditions.append(
                FieldCondition(key="erp", match=MatchValue(value=filters["erp"]))
            )

        if "date" in filters:
            date_filter = filters["date"]
            if isinstance(date_filter, dict):
                gte = date_filter.get("gte")
                lte = date_filter.get("lte")
                range_filter = {}
                if gte:
                    range_filter["gte"] = QdrantSystem.convert_to_timestamp(gte)
                if lte:
                    range_filter["lte"] = QdrantSystem.convert_to_timestamp(lte)
                if range_filter:  # Only add the condition if we have date filters
                    conditions.append(FieldCondition(key="created", range=Range(**range_filter)))


        return Filter(must=conditions) if conditions else None

    def _format_summary(self, content: Dict[str, Any]) -> str:
        """
        Formate la réponse en résumé bref
        
        Args:
            content: Contenu de la réponse
            
        Returns:
            Résumé bref
        """
        # Implémentation du formatage en résumé
        summary = content.get("summary", "")
        if not summary and "content" in content:
            # Si pas de résumé mais du contenu, on prend les 200 premiers caractères
            summary = content["content"][:200] + "..." if len(content["content"]) > 200 else content["content"]
        
        return summary
    
    def _format_detail(self, content: Dict[str, Any]) -> str:
        """
        Formate la réponse en explication complète
        
        Args:
            content: Contenu de la réponse
            
        Returns:
            Explication complète
        """
        # Implémentation du formatage en détail
        detail = ""
        
        # Titre ou résumé
        if "title" in content:
            detail += f"## {content['title']}\n\n"
        elif "summary" in content:
            detail += f"## {content['summary']}\n\n"
        
        # Contenu principal
        if "content" in content:
            detail += f"{content['content']}\n\n"
        elif "description" in content:
            detail += f"{content['description']}\n\n"
        elif "text" in content:
            detail += f"{content['text']}\n\n"
        
        # Informations supplémentaires
        if "comments" in content and content["comments"]:
            detail += f"### Commentaires\n{content['comments']}\n\n"
        # Ajouter le score
        if "score" in content:
            detail += f"Score de similarité : {content['score']}\n\n"
        # Métadonnées
        metadata = []
        if "created" in content:
            metadata.append(f"Créé le: {content['created']}")
        if "updated" in content:
            metadata.append(f"Mis à jour le: {content['updated']}")
        if "assignee" in content:
            metadata.append(f"Assigné à: {content['assignee']}")
        
        if metadata:
            detail += "---\n" + "\n".join(metadata)
        
        return detail
    
    def _format_guide(self, content: Dict[str, Any]) -> str:
        """
        Formate la réponse en instructions étape par étape
        
        Args:
            content: Contenu de la réponse
            
        Returns:
            Instructions étape par étape
        """
        # Implémentation du formatage en guide
        guide = ""
        
        # Titre
        if "title" in content:
            guide += f"# Guide: {content['title']}\n\n"
        elif "summary" in content:
            guide += f"# Guide: {content['summary']}\n\n"
        
        # Introduction
        if "description" in content:
            guide += f"## Introduction\n{content['description']}\n\n"
        
        # Contenu principal - on essaie de le structurer en étapes
        if "content" in content:
            # On tente de diviser le contenu en étapes
            steps = self._extract_steps(content["content"])
            if steps:
                guide += "## Étapes à suivre\n\n"
                for i, step in enumerate(steps, 1):
                    guide += f"{i}. {step}\n"
            else:
                guide += f"## Procédure\n{content['content']}\n\n"
        elif "text" in content:
            steps = self._extract_steps(content["text"])
            if steps:
                guide += "## Étapes à suivre\n\n"
                for i, step in enumerate(steps, 1):
                    guide += f"{i}. {step}\n"
            else:
                guide += f"## Procédure\n{content['text']}\n\n"
        
        # Notes ou conseils
        if "comments" in content and content["comments"]:
            guide += f"\n## Notes et conseils\n{content['comments']}\n"
        
        return guide
    
    def _extract_steps(self, text: str) -> List[str]:
        """
        Extrait les étapes d'un texte
        
        Args:
            text: Texte à analyser
            
        Returns:
            Liste des étapes extraites
        """
        # Recherche de patterns comme "1.", "Step 1:", "Étape 1:", etc.
        steps = []
        lines = text.split("\n")
        
        # Patterns possibles pour les étapes
        step_patterns = [
            r"^\d+\.",  # "1."
            r"^Step \d+:",  # "Step 1:"
            r"^Étape \d+:",  # "Étape 1:"
            r"^Étape \d+\.",  # "Étape 1."
        ]
        
        current_step = ""
        in_step = False
        
        for line in lines:
            is_step_header = any(pattern in line for pattern in step_patterns)
            
            if is_step_header:
                if in_step and current_step:
                    steps.append(current_step.strip())
                current_step = line
                in_step = True
            elif in_step:
                current_step += " " + line
        
        # Ajouter la dernière étape
        if in_step and current_step:
            steps.append(current_step.strip())
        
        # Si on n'a pas trouvé d'étapes avec les patterns, on essaie de diviser le texte
        if not steps and len(lines) > 3:
            # On divise le texte en paragraphes et on prend chaque paragraphe comme une étape
            paragraphs = []
            current_para = ""
            
            for line in lines:
                if line.strip():
                    current_para += line + " "
                elif current_para:
                    paragraphs.append(current_para.strip())
                    current_para = ""
            
            if current_para:
                paragraphs.append(current_para.strip())
            
            # Si on a entre 3 et 10 paragraphes, on les considère comme des étapes
            if 3 <= len(paragraphs) <= 10:
                steps = paragraphs
        
        return steps
    
    def create_response(self, query_result: Dict[str, Any], format_type: str = "Summary", collections_used: List[str] = None) -> Dict[str, str]:
        """
        Crée la réponse finale au format demandé
        
        Args:
            query_result: Résultat de la requête
            format_type: Format de la réponse (Summary, Detail, Guide)
            collections_used: Collections utilisées pour la requête
            
        Returns:
            Réponse formatée selon le template demandé
        """
        if not collections_used:
            collections_used = []
        
        content = self.format_response(query_result, format_type)
        
        return {
            "format": format_type,
            "content": content,
            "sources": ", ".join(collections_used)
        }
    def is_response_useless(self, text: str) -> bool:
        """
        Détecte si la réponse GPT est inutile ou trop vague
        """
        useless_patterns = [
            "je ne peux pas répondre", 
            "je ne suis pas sûr", 
            "je ne dispose pas", 
            "je n'ai pas assez d'informations", 
            "donnez plus de détails", 
            "veuillez préciser",
            "je suis un assistant", 
            "en tant qu'assistant", 
            "je ne suis pas capable"
        ]
        lower_text = text.lower()
        return any(p in lower_text for p in useless_patterns)

    def process_query(self, query, client_name=None, erp=None, recent_only=False, limit=5, format_type="Summary", raw=False, deepresearch=None):
    
        USE_EMBEDDING = os.getenv("USE_EMBEDDING", "true").lower() == "true"

        # Étape 1 : enrichissement de la requête via GPT
        enriched_query = self.enrich_query_with_openai(query)
        filters_dict = enriched_query.get("filters", {})
        erp = filters_dict.get("erp") or self.get_client_erp(filters_dict.get("client") or client_name)
        print(f"[🔍 DEBUG] ERP détecté après enrichissement : {erp}")


        # --- Vérification : ERP obligatoire pour requêtes fonctionnelles ---
        # Cette étape bloque les questions fonctionnelles sans ERP explicite
        functional_keywords = ["paramétrer", "configurer", "créer", "fournisseur", "client", "article", "facture", "guide"]
        if not erp and any(kw in query.lower() for kw in functional_keywords):
            raise ValueError("❌ Votre question semble concerner une fonctionnalité, mais l'ERP n'est pas précisé. Veuillez indiquer s'il s'agit de NetSuite ou SAP.")

        # --- Fin vérification ERP fonctionnel ---

        # 🔧 Correction importante : Définir systématiquement collections ici
        collections = enriched_query.get("collections") or self.get_prioritized_collections(client_name, erp)

        # Activation automatique du filtre recent_only selon le contexte
        if recent_only is False and any(w in query.lower() for w in ["récents", "derniers", "dernier ticket", "récent", "this week", "today"]):
            print("⏱️ Activation automatique du filtre 'recentOnly'")
            recent_only = True

        # Forçage pour le format Detail si aucune période n'est précisée
        if format_type == "Detail" and not filters_dict.get("period"):
            print("⏱️ Format 'Detail' sans période précisée : recentOnly forcé à True")
            recent_only = True

        # 💡 PATCH : Si la requête contient "ticket" mais pas d’ERP → on désactive deepresearch
        if deepresearch and not erp and "ticket" in query.lower():
            print("🔕 Aucun ERP détecté → Assistant GPT spécialisé désactivé pour cette requête.")
            deepresearch = False

        # 🔍 Activation automatique de deepresearch pour les questions fonctionnelles
        if deepresearch is None:
            deepresearch = format_type != "Detail"
            print(f"🔍 [DEBUG] Deepresearch activé pour le format {format_type} : {deepresearch}")


        # Étape 1bis : vérification de la qualité de la question
        if len(query.strip()) < 10:
            raise ValueError("❌ La question est trop courte pour une analyse pertinente.")
        # ❌ Blocage explicite du format Guide si la requête est trop vague
        if format_type == "Guide" and "ticket" in query.lower():
            guide_keywords = ["comment", "configurer", "résoudre", "procédure", "étapes", "corriger", "bug", "erreur", "solution"]
            if not any(kw in query.lower() for kw in guide_keywords):
                print("⚠️ Requête trop vague pour un guide. Passage automatique en mode 'Detail'.")
                format_type = "Detail"

        # Étape 2 : clé de cache
        filters_dict = enriched_query.get("filters", {})
        cache_key = self.cache.compute_key(query, filters_dict, limit)
        format_key = f"{format_type.upper()}:{cache_key}"

        print("\n🧠 [DEBUG] ➜ cache_key:", cache_key)
        print("🧠 [DEBUG] ➜ format_key:", format_key)

        all_results = self.cache.get_raw_results(cache_key)
        client_erp = self.get_client_erp(filters_dict.get("client")) if filters_dict.get("client") else None
        if not all_results:
            # Étape 3 : recherche dans Qdrant
            filters = self.apply_filters(filters_dict)
            limit = enriched_query.get("limit", limit)
            use_embedding = enriched_query.get("use_embedding", USE_EMBEDDING)

            all_results = []
            for collection_name in collections:
                try:
                    remaining = limit - len(all_results)
                    if remaining <= 0:
                        break
                    
                    if use_embedding:
                        results = self.search_in_collection(collection_name, query, client_name, recent_only, remaining, filters)
                        all_results.extend([
                            self.format_ticket_payload(payload, score, format_type)
                            for payload, score in results
                        ])
                    else:
                        raw_results = self.simple_filter_search(collection_name, client_name, recent_only, filters, remaining)
                        all_results.extend([
                            self.format_ticket_payload(payload, format_type=format_type)
                            for payload in raw_results
                        ])
                except Exception as e:
                    print(f"Erreur dans la collection {collection_name}: {str(e)}")

            all_results.sort(key=lambda r: r.get("created", ""), reverse=True)
            self.cache.store_raw_results(cache_key, query, filters_dict, limit, use_embedding, all_results)

        # Étape 4 : vérifie si format déjà calculé
        # 🧩 Patch : si format Detail + résultats trouvés → pas de GPT, on retourne les payloads
        if format_type == "Detail" and not deepresearch and all_results:
            return {
                "format": format_type,
                "content": all_results[:limit],
                "sources": ", ".join(collections),
                "meta": {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date"),
                    "use_embedding": use_embedding
                }
            }

        format_key = f"{format_type.upper()}:{cache_key}"
        cached_format = self.cache.get_format(format_key)

        if cached_format:
            print("✅ Format récupéré depuis le cache :", format_key)
            return {
                "format": format_type,
                "content": [cached_format["content"]] if isinstance(cached_format["content"], str) else cached_format["content"],
                "sources": cached_format["sources"],
                "meta": cached_format.get("meta", {})
            }
        else:
            print("🚫 [CACHE] Aucun format trouvé → on continue.")    
        # Étape 5 : deepresearch → GPT spécialisé + fusion
        if deepresearch:
            # --- Fonction utilitaire : détection de réponse hors sujet du GPT spécialisé ---
            def is_response_irrelevant(query: str, gpt_text: str) -> bool:
                """
                Compare si les mots clés significatifs de la question sont présents dans la réponse.
                Retourne True si la réponse est jugée hors sujet.
                """
                keywords = [w.lower() for w in query.split() if len(w) > 4]
                match_count = sum(1 for k in keywords if k in gpt_text.lower())
                relevance_ratio = match_count / max(len(keywords), 1)
                return relevance_ratio < 0.3  # seuil ajustable

            # Si le format est Summary et deepresearch est activé, traitement spécifique
            if format_type == "Summary":
                summaries = "\n".join(r.get("summary", "") for r in all_results[:limit])
                specialist_response = call_openai_assistant(erp, query)
                # --- Blocage si la réponse du GPT spécialisé est jugée hors sujet ---
                if is_response_irrelevant(query, specialist_response):
                    return {
                        "format": format_type,
                        "content": ["❌ La réponse du GPT spécialisé ne correspond pas à votre question. Veuillez reformuler ou préciser l'ERP concerné."],
                        "sources": ", ".join(collections),
                        "meta": {
                            "erp": filters_dict.get("erp") or client_erp,
                            "dateFilter": filters_dict.get("date"),
                            "mode": "deepresearch",
                            "use_embedding": use_embedding
                        }
                    }
                erp_label = client_erp or filters_dict.get("erp") or "l'ERP concerné"
                fusion_prompt = f"""Voici deux sources d'information sur la question suivante : \"{query}\""

                    1. Réponse du spécialiste ERP :
                    {specialist_response}

                    2. Résumé de tickets internes :
                    {summaries}

                    Fais une synthèse claire, complète et utile pour un utilisateur de {erp_label}."""

                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Tu es un assistant qui produit des synthèses enrichies à partir de sources internes et externes."},
                        {"role": "user", "content": fusion_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )

                summary_text = response.choices[0].message.content.strip()
                self.cache.store_format(format_key, "Summary", summary_text, ", ".join(collections), {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date"),
                    "mode": "deepresearch"
                })
                return {
                    "format": format_type,
                    "content": [summary_text],
                    "sources": ", ".join(collections),
                    "meta": {
                        "erp": filters_dict.get("erp") or client_erp,
                        "dateFilter": filters_dict.get("date"),
                        "mode": "deepresearch",
                        "use_embedding": use_embedding
                    }
                }
            # Sinon, traitement générique pour les autres formats avec deepresearch
            else:
                specialist_response = call_openai_assistant(erp, query)
                # --- Blocage si la réponse du GPT spécialisé est jugée hors sujet ---
                if is_response_irrelevant(query, specialist_response):
                    return {
                        "format": format_type,
                        "content": ["❌ La réponse du GPT spécialisé ne correspond pas à votre question. Veuillez reformuler ou préciser l'ERP concerné."],
                        "sources": ", ".join(collections),
                        "meta": {
                            "erp": filters_dict.get("erp") or client_erp,
                            "dateFilter": filters_dict.get("date"),
                            "mode": "deepresearch",
                            "use_embedding": use_embedding
                        }
                    }
                summaries = "\n".join(r.get("summary", "") for r in all_results[:limit])
                fusion_prompt = f"""Réponds à la question suivante à partir de deux sources complémentaires :\n\n1. Réponse du spécialiste ERP :\n\n{specialist_response}\n\n2. Données internes extraites des tickets et documentations :\n\n{summaries}\n\nRédige une réponse enrichie, claire et utile, en combinant les deux."""

                gpt_fused = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Tu combines les connaissances générales et les données internes pour produire une réponse enrichie."},
                        {"role": "user", "content": fusion_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                ).choices[0].message.content.strip()

                return {
                    "format": format_type,
                    "content": [gpt_fused],
                    "sources": ", ".join(collections),
                    "meta": {
                        "erp": filters_dict.get("erp") or client_erp,
                        "dateFilter": filters_dict.get("date"),
                        "mode": "deepresearch",
                        "use_embedding": use_embedding
                    }
                }

        # Étape 6 : traitement format classique (Summary, Guide, Detail)
        if format_type == "Summary" and not deepresearch:
            joined_summaries = "\n".join(r.get("summary", "") for r in all_results[:limit])
            prompt = f"Voici une liste de tickets utilisateurs concernant : {query}\n\n{joined_summaries}\n\nFais-en un résumé clair et concis."
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant expert en synthèse de tickets clients."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )
            summary_text = response.choices[0].message.content.strip()
            self.cache.store_format(format_key, "Summary", summary_text, ", ".join(collections), {
                "erp": filters_dict.get("erp") or client_erp,
                "dateFilter": filters_dict.get("date")
            })
            if self.is_response_useless(summary_text):
                return {
                "format": format_type,
                "content": ["❌ Aucun résumé utile n’a pu être généré à partir des données internes ou du GPT spécialisé."],
                "sources": ", ".join(collections),
                "meta": {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date"),
                    "mode": "deepresearch",
                    "use_embedding": use_embedding
                }
            }
            return {
                "format": format_type,
                "content": [summary_text],
                "sources": ", ".join(collections),
                "meta": {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date")
                }
            }

        elif format_type == "Guide":
            guide_input = "\n".join(r.get("summary", "") + "\n" + r.get("content", "") for r in all_results[:limit] if "content" in r)
            prompt = f"Voici des extraits de tickets. Rédige un guide pratique en étapes pour résoudre le problème évoqué :\n\n{guide_input}"
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui transforme des contenus de tickets en guide étape par étape."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            guide_text = response.choices[0].message.content.strip()

            if self.is_response_useless(guide_text):
                return {
                    "format": format_type,
                    "content": ["❌ Aucun guide utile n’a pu être généré à partir des données internes ou du GPT spécialisé."],
                    "sources": ", ".join(collections),
                    "meta": {
                        "erp": filters_dict.get("erp") or client_erp,
                        "dateFilter": filters_dict.get("date"),
                        "mode": "deepresearch",
                        "use_embedding": use_embedding
                    }
                }

            self.cache.store_format(
                format_key,
                "Guide",
                [guide_text],
                ", ".join(collections),
                {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date"),
                    "mode": "deepresearch"
                }
            )

            return {
                "format": format_type,
                "content": [guide_text],
                "sources": ", ".join(collections),
                "meta": {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date")
                }
            }


        # Sinon, traitement générique pour les autres formats avec deepresearch
        else:
            specialist_response = call_openai_assistant(erp, query)
            summaries = "\n".join(r.get("summary", "") for r in all_results[:limit])
            fusion_prompt = f"""Réponds à la question suivante à partir de deux sources complémentaires :\n\n1. Réponse du spécialiste ERP :\n\n{specialist_response}\n\n2. Données internes extraites des tickets et documentations :\n\n{summaries}\n\nRédige une réponse enrichie, claire et utile, en combinant les deux."""

            gpt_fused = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu combines les connaissances générales et les données internes pour produire une réponse enrichie."},
                    {"role": "user", "content": fusion_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            ).choices[0].message.content.strip()
            gpt_fused = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu combines les connaissances générales et les données internes pour produire une réponse enrichie."},
                    {"role": "user", "content": fusion_prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            ).choices[0].message.content.strip()

            if format_type == "Detail":
                # Stockage systématique du format Detail généré par GPT dans le cache
                self.cache.store_format(
                    format_key,
                    "Detail",
                    [{
                        "summary": gpt_fused,
                        "created": None,
                        "updated": None,
                        "source": "GPT",
                        "assignee": None,
                        "url": None,
                        "score": None
                    }],
                    ", ".join(collections),
                    {
                        "erp": filters_dict.get("erp") or client_erp,
                        "dateFilter": filters_dict.get("date"),
                        "mode": "deepresearch"
                    }
                )
                print(f"✅ Format stocké dans le cache : DETAIL:{format_key}")

                return {
                    "format": format_type,
                    "content": [{
                        "summary": gpt_fused,
                        "created": None,
                        "updated": None,
                        "source": "GPT",
                        "assignee": None,
                        "url": None,
                        "score": None
                    }],
                    "sources": ", ".join(collections),
                    "meta": {
                        "erp": filters_dict.get("erp") or client_erp,
                        "dateFilter": filters_dict.get("date"),
                        "mode": "deepresearch",
                        "use_embedding": use_embedding
                    }
                }

            # Sinon (ex: Guide), retour classique texte enrichi
            return {
                "format": format_type,
                "content": [gpt_fused],
                "sources": ", ".join(collections),
                "meta": {
                    "erp": filters_dict.get("erp") or client_erp,
                    "dateFilter": filters_dict.get("date"),
                    "mode": "deepresearch",
                    "use_embedding": use_embedding
                }
            }





# Fonction principale pour tester le système
def main():
    """Fonction principale pour tester le système"""
    clients_file = "/home/ubuntu/upload/ListeClients.csv"
    system = QdrantSystem(clients_file)
    
    # Test avec un client SAP
    client_name = "AZERGO"
    print(f"Client: {client_name}")
    print(f"ERP: {system.get_client_erp(client_name)}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(client_name)}")
    
    # Test avec un client NetSuite
    client_name = "ADVIGO"
    print(f"\nClient: {client_name}")
    print(f"ERP: {system.get_client_erp(client_name)}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(client_name)}")
    
    # Test avec un ERP sans client
    erp = "NetSuite"
    print(f"\nERP: {erp}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(erp=erp)}")

if __name__ == "__main__":
    main()
