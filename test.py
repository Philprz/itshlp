#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour le programme client Qdrant
Ce script teste les fonctionnalités du programme client Qdrant
"""

import os
import json
from main import QdrantSystem

def test_connection():
    """Teste la connexion à Qdrant"""
    print("=== Test de connexion à Qdrant ===")
    try:
        # Initialisation du système
        clients_file = "/home/ubuntu/upload/ListeClients.csv"
        system = QdrantSystem(clients_file)
        print("✓ Connexion à Qdrant réussie")
        return system
    except Exception as e:
        print(f"✗ Erreur de connexion à Qdrant: {e}")
        return None

def test_client_info(system):
    """Teste la récupération des informations client"""
    print("\n=== Test de récupération des informations client ===")
    
    # Test avec un client SAP
    client_name = "AZERGO"
    client_info = system.get_client_info(client_name)
    print(f"Client: {client_name}")
    print(f"ERP: {system.get_client_erp(client_name)}")
    print(f"Informations: {json.dumps(client_info, indent=2, ensure_ascii=False)}")
    
    # Test avec un client NetSuite
    client_name = "ADVIGO"
    client_info = system.get_client_info(client_name)
    print(f"\nClient: {client_name}")
    print(f"ERP: {system.get_client_erp(client_name)}")
    print(f"Informations: {json.dumps(client_info, indent=2, ensure_ascii=False)}")

def test_prioritized_collections(system):
    """Teste la priorisation des collections"""
    print("\n=== Test de priorisation des collections ===")
    
    # Test avec un client SAP
    client_name = "AZERGO"
    print(f"Client: {client_name}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(client_name)}")
    
    # Test avec un client NetSuite
    client_name = "ADVIGO"
    print(f"\nClient: {client_name}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(client_name)}")
    
    # Test avec un ERP sans client
    erp = "NetSuite"
    print(f"\nERP: {erp}")
    print(f"Collections prioritaires: {system.get_prioritized_collections(erp=erp)}")

def test_search(system):
    """Teste la recherche dans les collections"""
    print("\n=== Test de recherche dans les collections ===")
    
    try:
        # Test de recherche pour un client spécifique
        query_result = system.process_query(
            query_text="Problèmes de connexion",
            client_name="AZERGO",
            recent_only=True,
            limit=2,
            format_type="Summary"
        )
        
        print("Résultat de la recherche pour 'Problèmes de connexion' (client: AZERGO):")
        print(json.dumps(query_result, indent=2, ensure_ascii=False))
        
        # Test de recherche pour un ERP spécifique
        query_result = system.process_query(
            query_text="Configuration comptabilité",
            erp="NetSuite",
            recent_only=False,
            limit=2,
            format_type="Detail"
        )
        
        print("\nRésultat de la recherche pour 'Configuration comptabilité' (ERP: NetSuite):")
        print(json.dumps(query_result, indent=2, ensure_ascii=False))
        
        # Test de recherche avec requête ambiguë
        query_result = system.process_query(
            query_text="Comment configurer",
            recent_only=True,
            limit=2,
            format_type="Guide"
        )
        
        print("\nRésultat de la recherche pour 'Comment configurer' (requête ambiguë):")
        print(json.dumps(query_result, indent=2, ensure_ascii=False))
        
        return True
    except Exception as e:
        print(f"✗ Erreur lors de la recherche: {e}")
        return False

def test_formatting(system):
    """Teste le formatage des réponses"""
    print("\n=== Test de formatage des réponses ===")
    
    # Création d'un contenu de test
    test_content = {
        "title": "Test de formatage",
        "summary": "Résumé du test de formatage",
        "content": "Contenu détaillé du test de formatage.\n\nCe contenu est utilisé pour tester les différents formats de réponse.\n\nÉtape 1: Première étape\nÉtape 2: Deuxième étape\nÉtape 3: Troisième étape",
        "description": "Description du test de formatage",
        "comments": "Commentaires sur le test de formatage",
        "created": "2025-03-15",
        "updated": "2025-03-30",
        "assignee": "Test User"
    }
    
    # Test du format Summary
    summary = system.format_response(test_content, "Summary")
    print("Format Summary:")
    print(summary)
    
    # Test du format Detail
    detail = system.format_response(test_content, "Detail")
    print("\nFormat Detail:")
    print(detail)
    
    # Test du format Guide
    guide = system.format_response(test_content, "Guide")
    print("\nFormat Guide:")
    print(guide)

def main():
    """Fonction principale pour les tests"""
    print("Démarrage des tests du programme client Qdrant...\n")
    
    # Test de connexion
    system = test_connection()
    if not system:
        print("Impossible de continuer les tests sans connexion à Qdrant.")
        return
    
    # Test des informations client
    test_client_info(system)
    
    # Test de priorisation des collections
    test_prioritized_collections(system)
    
    # Test de formatage des réponses
    test_formatting(system)
    
    # Test de recherche
    search_success = test_search(system)
    
    print("\n=== Résumé des tests ===")
    print("✓ Connexion à Qdrant")
    print("✓ Récupération des informations client")
    print("✓ Priorisation des collections")
    print("✓ Formatage des réponses")
    print(f"{'✓' if search_success else '✗'} Recherche dans les collections")
    
    print("\nTests terminés.")

if __name__ == "__main__":
    main()
