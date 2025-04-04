#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Système de requêtes pour les collections Qdrant d'IT SPIRIT
Ce système permet d'interroger les collections Qdrant selon les priorités définies
et de formater les réponses selon les formats demandés.
"""

import csv
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
from qdrant_client.http.models import FieldCondition, MatchValue, Range, Filter

# Chargement des variables d'environnement
load_dotenv()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Définition du prompt système pour OpenAI
system_prompt = """Tu es un assistant spécialisé dans l'analyse de requêtes pour le système de recherche IT SPIRIT.
Analyse la requête de l'utilisateur et structure-la en JSON avec les éléments suivants:
- collections: Liste des collections à rechercher (parmi JIRA, CONFLUENCE, ZENDESK, NETSUITE, NETSUITE_DUMMIES, SAP)
- filters: Dictionnaire de filtres (client, erp, date, etc.)
- use_embedding: Booléen indiquant s'il faut utiliser l'embedding pour la recherche
- limit: Nombre de résultats à retourner
"""
# Définition des collections
COLLECTIONS = ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES", "SAP"]

# Définition des formats de réponse
FORMATS = ["Summary", "Detail", "Guide"]

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
    #vérifier si cela a changé ?    
    def enrich_query_with_openai(self, user_query):
        response = openai_client.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.0,
            max_tokens=300
        )
        
        enriched_query = response.choices[0].message.content.strip()

        try:
            enriched_json = json.loads(enriched_query)
        except json.JSONDecodeError as e:
            raise ValueError(f"Réponse GPT non conforme : {enriched_query}") from e

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
    def simple_filter_search(self, collection_name, client_name=None, recent_only=False, limit=5):
        filter_conditions = []

        if client_name:
            filter_conditions.append(
                FieldCondition(
                    key="client",
                    match=MatchValue(value=client_name)
                )
            )

        if recent_only:
            six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
            filter_conditions.append(
                FieldCondition(
                    key="created",
                    range=Range(gte=six_months_ago)
                )
            )

        search_filter = Filter(must=filter_conditions) if filter_conditions else None

        search_result = self.client.scroll(
            collection_name=self.collections[collection_name],
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True
        )

        return [hit.payload for hit in search_result[0]]
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
            Liste des documents pertinents (payloads)
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

        return [hit.payload for hit in results]

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
                if gte or lte:
                    range_filter = {}
                    if gte:
                        range_filter["gte"] = gte
                    if lte:
                        range_filter["lte"] = lte
                    conditions.append(
                        FieldCondition(key="created", range=Range(**range_filter))
                    )

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
    def process_query(self, query, client_name=None, erp=None, recent_only=True, limit=5, format_type="Summary"):
        """
        Traite une requête utilisateur et renvoie les résultats formatés.
        """
        # Chargement du paramètre global d'embedding depuis .env
        USE_EMBEDDING = os.getenv("USE_EMBEDDING", "true").lower() == "true"

        enriched_query = self.enrich_query_with_openai(query)

        # Collections à rechercher
        collections = enriched_query.get("collections", self.get_prioritized_collections(client_name, erp))

        # Filtres Qdrant construits à partir de la réponse enrichie
        filters = self.apply_filters(enriched_query.get("filters", {}))

        # Limite de résultats à retourner
        limit = enriched_query.get("limit", limit)

        # Priorité de l'embedding (prend celui de l'enrichissement s'il existe, sinon celui du .env)
        use_embedding = enriched_query.get("use_embedding", USE_EMBEDDING)

        all_results = []

        for collection_name in collections:
            try:
                if use_embedding:
                    results = self.search_in_collection(
                        collection_name=collection_name,
                        query=query,
                        client_name=client_name,
                        recent_only=recent_only,
                        limit=limit,
                        filters=filters
                    )
                else:
                    results = self.simple_filter_search(
                        collection_name=collection_name,
                        client_name=client_name,
                        recent_only=recent_only,
                        limit=limit
                    )

                all_results.extend(results)
                if len(all_results) >= limit:
                    break
            except Exception as e:
                print(f"Erreur dans la collection {collection_name}: {str(e)}")

        if not all_results:
            return {
                "format": format_type,
                "content": ["Aucun résultat trouvé pour cette requête."],
                "sources": ", ".join(collections)
            }

        return {
            "format": format_type,
            "content": [self.format_response(r, format_type) for r in all_results[:limit]],
            "sources": ", ".join(collections)
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
