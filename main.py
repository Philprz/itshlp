#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Programme client Qdrant pour IT SPIRIT
Ce programme permet d'interroger les collections Qdrant contenant des informations
sur les clients IT SPIRIT et les systèmes ERP (SAP et NetSuite).
"""

import os
import re
import csv
from datetime import datetime, timedelta
from typing import List, Dict, Any
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
        
        Args:
            clients_file: Chemin vers le fichier CSV contenant les informations clients
        """
        self.clients = self._load_clients(clients_file)
        self.collections = COLLECTIONS
        self.formats = FORMATS
        self.client = self._connect_to_qdrant()
    def _analyze_query_patterns(self, query):
        """
        Analyse la requête pour détecter des patterns spécifiques et extraire des informations.
        
        Args:
            query (str): La requête de l'utilisateur
            
        Returns:
            dict: Informations extraites de la requête (client, erp, type de demande, etc.)
        """
        query_lower = query.lower()
        extracted_info = {
            "client": None,
            "erp": None,
            "is_ticket_request": False,
            "recent_only": True,  # Par défaut, on cherche les tickets récents
            "limit": 5  # Par défaut, on limite à 5 tickets
        }
        
        # Détecter les patterns de type "tickets [CLIENT]" (utiliser search au lieu de match)
        ticket_client_pattern = re.search(r"tickets?\s+(\w+)", query_lower)
        if ticket_client_pattern:
            client_name = ticket_client_pattern.group(1).upper()
            extracted_info["client"] = client_name
            extracted_info["is_ticket_request"] = True
            
            # Vérifier si le client existe dans notre liste
            if self._client_exists(client_name):
                print(f"Client trouvé: {client_name}")
            else:
                print(f"Client non trouvé dans la liste: {client_name}, mais on continue la recherche")
        
        # Détecter les clients mentionnés en fin de phrase
        if not extracted_info["client"]:
            client_pattern = re.search(r"\b(\w+)$", query_lower)
            if client_pattern:
                potential_client = client_pattern.group(1).upper()
                # Vérifier si c'est un client connu
                if self._client_exists(potential_client):
                    extracted_info["client"] = potential_client
                    print(f"Client détecté en fin de phrase: {potential_client}")
        
        # Détecter les mentions d'ERP
        if "sap" in query_lower:
            extracted_info["erp"] = "SAP"
        elif "netsuite" in query_lower or "net suite" in query_lower:
            extracted_info["erp"] = "NetSuite"
        
        # Détecter les mentions de période
        if "dernier" in query_lower or "récent" in query_lower:
            extracted_info["recent_only"] = True
        
        # Détecter les mentions de quantité
        quantity_pattern = re.search(r"(\d+)\s+tickets", query_lower)
        if quantity_pattern:
            try:
                extracted_info["limit"] = int(quantity_pattern.group(1))
            except ValueError:
                pass  # On garde la valeur par défaut
        
        # Détecter si la requête concerne des tickets même si le mot "ticket" n'est pas explicitement mentionné
        if "problème" in query_lower or "incident" in query_lower or "demande" in query_lower:
            extracted_info["is_ticket_request"] = True
        
        return extracted_info
    def _client_exists(self, client_name):
        """
        Vérifie si un client existe dans notre liste de clients.
        
        Args:
            client_name (str): Nom du client à vérifier
            
        Returns:
            bool: True si le client existe, False sinon
        """
        # Charger la liste des clients depuis le fichier CSV
        try:
            client_list_path = os.path.join(os.path.dirname(__file__), "ListeClients.csv")
            if os.path.exists(client_list_path):
                with open(client_list_path, "r", encoding="utf-8") as f:
                    clients = [line.strip().upper() for line in f.readlines()]
                return client_name.upper() in clients
            return False
        except Exception as e:
            print(f"Erreur lors de la vérification du client: {e}")
            return False
    def _get_prioritized_collections(self, client_name=None, erp=None, query=None):
        """
        Détermine l'ordre de priorité des collections à interroger.
        
        Args:
            client_name (str, optional): Nom du client. Defaults to None.
            erp (str, optional): ERP spécifique. Defaults to None.
            query (str, optional): Requête utilisateur pour analyse contextuelle. Defaults to None.
            
        Returns:
            list: Liste des collections dans l'ordre de priorité
        """
        # Si la requête contient "ticket" et un client est spécifié, prioriser les collections de tickets
        if query and ("ticket" in query.lower() or "problème" in query.lower() or "incident" in query.lower()) and client_name:
            return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Si un ERP est spécifié, prioriser les collections correspondantes
        if erp == "SAP":
            return ["SAP", "JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES"]
        elif erp == "NetSuite":
            return ["NETSUITE", "NETSUITE_DUMMIES", "JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
        
        # Si un client est spécifié mais pas d'ERP, prioriser les collections de clients
        if client_name:
            return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Par défaut, prioriser les collections les plus récentes
        return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
    def process_query(self, query, client_name=None, erp=None, recent_only=False, limit=5, format_type="Summary"):
        """
        Traite une requête utilisateur et renvoie les résultats formatés.
        
        Args:
            query (str): La requête de l'utilisateur
            client_name (str, optional): Nom du client. Defaults to None.
            erp (str, optional): ERP spécifique (SAP ou NetSuite). Defaults to None.
            recent_only (bool, optional): Limiter aux résultats récents. Defaults to False.
            limit (int, optional): Nombre maximum de résultats. Defaults to 5.
            format_type (str, optional): Type de formatage (Summary, Detail, Guide). Defaults to "Summary".
            
        Returns:
            dict: Résultats formatés
        """
        # Vérifier que la requête n'est pas vide
        if not query:
            return {
                "format": format_type,
                "content": ["Veuillez entrer une requête de recherche"],
                "sources": ""
            }
        
        # Ajouter des logs pour le débogage
        print(f"Requête reçue: {query}")
        print(f"Client initial: {client_name}")
        print(f"ERP initial: {erp}")
        
        # Analyser les patterns dans la requête
        extracted_info = self._analyze_query_patterns(query)
        
        # Utiliser les informations extraites si elles ne sont pas déjà spécifiées
        if not client_name and extracted_info["client"]:
            client_name = extracted_info["client"]
            print(f"Client détecté dans la requête: {client_name}")
        
        if not erp and extracted_info["erp"]:
            erp = extracted_info["erp"]
            print(f"ERP détecté dans la requête: {erp}")
        
        # Pour les requêtes de tickets, forcer recent_only à True par défaut
        if extracted_info["is_ticket_request"]:
            recent_only = extracted_info.get("recent_only", True)
            limit = extracted_info.get("limit", 5)
            print(f"Requête de tickets détectée: recent_only={recent_only}, limit={limit}")
        
        # Supprimer complètement la vérification d'ambiguïté
        # Ne plus vérifier si la requête est ambiguë
        
        # Récupération des collections prioritaires
        collections = self._get_prioritized_collections(client_name, erp, query)
        print(f"Collections prioritaires: {collections}")
        
        # Recherche dans chaque collection
        all_results = []
        collections_used = []
        
        for collection_name in collections:
            try:
                print(f"Recherche dans la collection {collection_name}...")
                results = self._search_in_collection(
                    collection_name,
                    query,
                    client_name=client_name,
                    recent_only=recent_only,
                    limit=limit
                )
                
                if results:
                    print(f"Résultats trouvés dans {collection_name}: {len(results)}")
                    all_results.extend(results)
                    collections_used.append(collection_name)
                    
                    # Si on a suffisamment de résultats, on s'arrête
                    if len(all_results) >= limit:
                        break
                else:
                    print(f"Aucun résultat trouvé dans {collection_name}")
            except Exception as e:
                print(f"Erreur lors de la recherche dans {collection_name}: {e}")
                continue
        
        # Limiter le nombre de résultats
        all_results = all_results[:limit]
        print(f"Nombre total de résultats: {len(all_results)}")
        
        # Si aucun résultat n'est trouvé, suggérer des améliorations sans bloquer
        if not all_results:
            suggestions = [
                "Essayez d'ajouter plus de détails à votre requête",
                "Précisez le nom du client si vous recherchez des informations spécifiques à un client",
                "Mentionnez explicitement SAP ou NetSuite si votre question concerne un ERP spécifique"
            ]
            
            # Ajouter des suggestions spécifiques en fonction du contexte
            if client_name:
                suggestions.append(f"Essayez une requête plus générale sans spécifier le client {client_name}")
            if erp:
                suggestions.append(f"Essayez une requête plus générale sans spécifier l'ERP {erp}")
            
            return {
                "format": format_type,
                "content": ["Aucun résultat trouvé. Essayez de préciser votre requête ou d'utiliser d'autres termes de recherche."],
                "sources": "",
                "suggestions": suggestions
            }
        
        # Formater les résultats
        formatted_results = [self._format_response(result, format_type) for result in all_results]
        
        return {
            "format": format_type,
            "content": formatted_results,
            "sources": ", ".join(collections_used)
        }

    def _connect_to_qdrant(self) -> QdrantClient:
        """
        Établit la connexion avec Qdrant
        
        Returns:
            Client Qdrant
        """
        try:
            client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
            print("Connexion à Qdrant établie avec succès")
            return client
        except Exception as e:
            print(f"Erreur lors de la connexion à Qdrant: {e}")
            raise
        
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
                    # Si on ne connaît toujours pas l'ERP, on renvoie toutes les collections
                    return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Si on a un ERP mais pas de client
        if erp == "SAP":
            return ["SAP", "JIRA", "CONFLUENCE", "ZENDESK"]
        elif erp == "NetSuite":
            return ["NETSUITE", "NETSUITE_DUMMIES", "JIRA", "CONFLUENCE", "ZENDESK"]
        
        # Si on n'a ni client ni ERP, on renvoie toutes les collections
        return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
    def _get_prioritized_collections(self, client_name=None, erp=None, query=None):
        """
        Détermine les collections à interroger en priorité en fonction du client, de l'ERP et de la requête.
        
        Args:
            client_name (str, optional): Nom du client. Defaults to None.
            erp (str, optional): ERP spécifique (SAP ou NetSuite). Defaults to None.
            query (str, optional): Requête utilisateur. Defaults to None.
            
        Returns:
            list: Liste des collections à interroger, par ordre de priorité
        """
        # Analyser la requête pour détecter des mentions d'ERP
        if query:
            query_lower = query.lower()
            mentions_sap = "sap" in query_lower
            mentions_netsuite = "netsuite" in query_lower or "net suite" in query_lower
            
            # Si la requête mentionne explicitement un ERP, le prioriser
            if mentions_sap:
                return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
            elif mentions_netsuite:
                return ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Sinon, utiliser l'ERP sélectionné s'il y en a un
        if erp == "SAP":
            return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
        elif erp == "NetSuite":
            return ["NETSUITE", "NETSUITE_DUMMIES", "JIRA", "CONFLUENCE", "ZENDESK"]
        
        # Si on a un client mais pas d'ERP spécifié
        if client_name:
            # Vérifier si le client a un ERP spécifique dans les données client
            client_erp = self.get_client_erp(client_name)
            if client_erp == "SAP":
                return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP"]
            elif client_erp == "NetSuite":
                return ["JIRA", "CONFLUENCE", "ZENDESK", "NETSUITE", "NETSUITE_DUMMIES"]
            else:
                # Si on ne connaît pas l'ERP, chercher dans toutes les collections
                return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]
        
        # Par défaut, chercher dans toutes les collections
        return ["JIRA", "CONFLUENCE", "ZENDESK", "SAP", "NETSUITE", "NETSUITE_DUMMIES"]

    def is_recent_date(self, date_str: str) -> bool:
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
        except ValueError:
            return False
    
    def search_in_collection(self, collection_name: str, query: str, client_name: str = "", 
                            recent_only: bool = False, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche dans une collection Qdrant
        
        Args:
            collection_name: Nom de la collection
            query: Requête de recherche
            client_name: Nom du client (optionnel)
            recent_only: Filtrer uniquement les résultats récents (moins de 6 mois)
            limit: Nombre maximum de résultats à retourner
            
        Returns:
            Liste des résultats de la recherche
        """
        try:
            # Préparation des filtres
            filter_conditions = []
            
            # Filtre par client si spécifié
            if client_name:
                filter_conditions.append(
                    FieldCondition(
                        key="client",
                        match=MatchValue(value=client_name)
                    )
                )
            
            # Filtre par date si recent_only est True
            # Note: Désactivé pour le prototype car peut causer des erreurs
            if False and recent_only:
                six_months_ago = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
                filter_conditions.append(
                    FieldCondition(
                        key="created",
                        range=Range(
                            gte=six_months_ago
                        )
                    )
                )
            
            # Construction du filtre final
            search_filter = None
            if filter_conditions:
                search_filter = Filter(
                    must=filter_conditions
                )
            
            # Simulation de vecteur d'embedding pour la requête
            # Dans une implémentation réelle, nous utiliserions un modèle d'embedding
            import numpy as np
            query_vector = np.random.rand(1536).tolist()
            
            # Exécution de la recherche
            search_result = self.client.search(
                collection_name=self.collections[collection_name],
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit
            )
            
            # Conversion des résultats
            return [hit.payload for hit in search_result]
        except Exception as e:
            print(f"Erreur lors de la recherche dans la collection {collection_name}: {e}")
            return []
    
    def is_query_ambiguous(self, query: str, client_name: str, erp: str) -> bool:
        """
        Vérifie si une requête est ambiguë
        
        Args:
            query: Requête de recherche
            client_name: Nom du client (optionnel)
            erp: Système ERP (optionnel)
            
        Returns:
            True si la requête est ambiguë, False sinon
        """
        # Si on n'a pas de client ni d'ERP et que la requête ne les mentionne pas
        if not client_name and not erp:
            # Vérifier si la requête mentionne un ERP
            erp_mentioned = "SAP" in query or "NetSuite" in query
            
            if not erp_mentioned:
                return True
        
        return False
    
    def _format_response(self, result, format_type="Summary"):
        """
        Formate un résultat selon le type de formatage demandé.
        
        Args:
            result (dict): Résultat à formater
            format_type (str, optional): Type de formatage (Summary, Detail, Guide). Defaults to "Summary".
            
        Returns:
            str: Résultat formaté
        """
        # Extraire les informations du résultat
        title = result.get("title", "Sans titre")
        content = result.get("content", "")
        created_at = result.get("created_at", 0)
        updated_at = result.get("updated_at", 0)
        author = result.get("author", "")
        
        # Formater les dates en jj/mm/aa
        created_date = self._format_date(created_at)
        updated_date = self._format_date(updated_at)
        
        # Formater selon le type demandé
        if format_type == "Summary":
            return f"{title} - {created_date}"
        
        elif format_type == "Detail":
            return f"{title}\n\nCréé le: {created_date}\nMis à jour le: {updated_date}\nAuteur: {author}\n\n{content[:200]}..."
        
        elif format_type == "Guide":
            # Extraire les étapes du contenu
            steps = re.findall(r"(\d+\.\s+[^\n]+)", content)
            formatted_steps = "\n".join(steps[:5]) if steps else "Aucune étape identifiée"
            
            return f"{title}\n\nÉtapes principales:\n{formatted_steps}\n\nCréé le: {created_date}"
        
        # Par défaut, renvoyer un résumé
        return f"{title} - {created_date}"
    def _format_date(self, timestamp):
        """
        Formate un timestamp Unix en date lisible au format jj/mm/aa.
        
        Args:
            timestamp (int): Timestamp Unix
            
        Returns:
            str: Date formatée
        """
        if not timestamp:
            return "Date inconnue"
        
        try:
            # Convertir le timestamp en date
            date = datetime.datetime.fromtimestamp(int(timestamp))
            # Formater la date en jj/mm/aa
            return date.strftime("%d/%m/%y")
        except Exception as e:
            print(f"Erreur lors du formatage de la date: {e}")
            return "Date invalide"

    def _format_summary(self, content: Dict[str, Any]) -> str:
        """
        Formate la réponse en résumé bref
        
        Args:
            content: Contenu de la réponse
            
        Returns:
            Résumé bref
        """
        # Implémentation du formatage en résumé
        if "summary" in content and content["summary"]:
            return content["summary"]
        
        if "content" in content and content["content"]:
            # Si pas de résumé mais du contenu, on prend les 200 premiers caractères
            text = content["content"]
            if len(text) > 200:
                return text[:200] + "..."
            return text
        
        if "title" in content and content["title"]:
            return content["title"]
        
        if "description" in content and content["description"]:
            text = content["description"]
            if len(text) > 200:
                return text[:200] + "..."
            return text
        
        return "Aucun résumé disponible"
    
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
        if "title" in content and content["title"]:
            detail += f"## {content['title']}\n\n"
        elif "summary" in content and content["summary"]:
            detail += f"## {content['summary']}\n\n"
        
        # Contenu principal
        if "content" in content and content["content"]:
            detail += f"{content['content']}\n\n"
        elif "description" in content and content["description"]:
            detail += f"{content['description']}\n\n"
        elif "text" in content and content["text"]:
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
        
        import re
        current_step = ""
        in_step = False
        
        for line in lines:
            is_step_header = any(re.match(pattern, line) for pattern in step_patterns)
            
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
                return paragraphs
        
        return steps
