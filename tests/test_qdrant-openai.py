#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de test pour vérifier la connexion à Qdrant et OpenAI
Ce script vérifie la connexion à Qdrant, liste les collections disponibles
et teste la création d'embeddings avec OpenAI.
"""

import os
import sys
from dotenv import load_dotenv
import traceback

def print_section(title: str):
    """Affiche un titre de section formaté"""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)


# Test Qdrant
def test_qdrant_connection():
    """Teste la connexion à Qdrant et liste les collections disponibles"""
    print_section("TEST DE CONNEXION À QDRANT")
    
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http.exceptions import UnexpectedResponse
        
        # Récupération des variables d'environnement
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        
        # Vérification des variables d'environnement
        if not qdrant_url:
            print("❌ Erreur: Variable d'environnement QDRANT_URL non définie")
            return False
        
        print(f"🔍 Tentative de connexion à Qdrant: {qdrant_url}")
        
        # Création du client Qdrant
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        
        # Test de connexion en récupérant la liste des collections
        collections = client.get_collections().collections
        
        if not collections:
            print("⚠️ Connexion réussie mais aucune collection trouvée")
            return True
        
        print("✅ Connexion à Qdrant établie avec succès!")
        print("📊 Nombre de collections trouvées: {len(collections)}")
        
        # Affichage des informations sur chaque collection
        for i, collection in enumerate(collections, 1):
            collection_name = collection.name
            print(f"\n📁 Collection {i}: {collection_name}")
            
            try:
                # Récupération des informations sur la collection
                collection_info = client.get_collection(collection_name=collection_name)
                
                # Récupération du nombre de points dans la collection
                count = client.count(collection_name=collection_name).count
                
                print(f"  - Points: {count:,}")
                print(f"  - Vecteurs: {collection_info.config.params.vectors}")
                print(f"  - Type de vecteur: {collection_info.config.params.vectors.size} dimensions")
                
                # Récupération des champs de payload (facultatif)
                try:
                    # Récupération d'un échantillon pour voir la structure
                    if count > 0:
                        sample = client.retrieve(collection_name=collection_name, ids=[0], with_payload=True, limit=1)
                        if sample:
                            payload_keys = list(sample[0].payload.keys()) if sample[0].payload else []
                            print(f"  - Champs de payload: {', '.join(payload_keys[:10])}{'...' if len(payload_keys) > 10 else ''}")
                except Exception as e:
                    print(f"  - Erreur lors de la récupération des champs de payload: {str(e)}")
            
            except Exception as e:
                print(f"  - ❌ Erreur lors de la récupération des informations: {str(e)}")
        
        return True
    
    except ImportError:
        print("❌ Erreur: Module qdrant_client non installé. Installez-le avec:")
        print("   pip install qdrant-client")
        return False
    
    except UnexpectedResponse as e:
        print(f"❌ Erreur de réponse Qdrant: {str(e)}")
        print("   Vérifiez l'URL et la clé API")
        return False
    
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à Qdrant: {str(e)}")
        traceback.print_exc()
        return False


# Test OpenAI
def test_openai_connection():
    """Teste la connexion à OpenAI pour la création d'embeddings"""
    print_section("TEST DE CONNEXION À OPENAI")
    
    try:
        import openai
        
        # Récupération de la clé API OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            print("❌ Erreur: Variable d'environnement OPENAI_API_KEY non définie")
            return False
        
        print("🔍 Tentative de connexion à OpenAI...")
        
        # Configuration du client OpenAI
        client = openai.OpenAI(api_key=api_key)
        
        # Test de la création d'embeddings
        test_text = "Ceci est un test de connexion à OpenAI pour vérifier la création d'embeddings."
        
        print(f"📝 Génération d'embedding pour le texte: '{test_text[:30]}...'")
        
        try:
            # Utilisation de la nouvelle syntaxe OpenAI
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=test_text
            )
            
            # Vérification de la réponse
            embedding = response.data[0].embedding
            embedding_dim = len(embedding)
            
            print("✅ Embedding généré avec succès!")
            print(f"📊 Dimensions de l'embedding: {embedding_dim}")
            print(f"🔢 Premiers éléments: {embedding[:5]}...")
            
            # Test d'une requête de complétion
            print("\n📝 Test de complétion de texte...")
            
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Vous êtes un assistant utile."},
                    {"role": "user", "content": "Dites bonjour en français."}
                ]
            )
            
            response_text = completion.choices[0].message.content
            print(f"✅ Complétion réussie: '{response_text}'")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération de l'embedding: {str(e)}")
            traceback.print_exc()
            return False
            
    except ImportError:
        print("❌ Erreur: Module openai non installé. Installez-le avec:")
        print("   pip install openai")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la connexion à OpenAI: {str(e)}")
        traceback.print_exc()
        return False


# Test de concrétion (requête → embedding → recherche Qdrant → résultats)
def test_full_query_process():
    """
    Teste le processus complet d'une requête:
    1. Génération d'embedding avec OpenAI
    2. Recherche dans Qdrant avec cet embedding
    3. Récupération et affichage des résultats
    """
    print_section("TEST DE CONCRÉTION: REQUÊTE COMPLÈTE")
    
    try:
        import openai
        from qdrant_client import QdrantClient
        
        # Récupération des variables d'environnement
        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if not qdrant_url or not openai_api_key:
            print("❌ Erreur: Variables d'environnement manquantes")
            return False
        
        # 1. Création des clients
        print("🔍 Initialisation des clients...")
        qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
        openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # 2. Récupération des collections disponibles
        collections = qdrant_client.get_collections().collections
        if not collections:
            print("⚠️ Aucune collection trouvée dans Qdrant")
            return False
        
        # Utilisation de la première collection pour le test
        test_collection = collections[0].name
        print(f"📁 Utilisation de la collection: {test_collection}")
        
        # 3. Création d'une requête de test
        test_query = "problème de connexion à SAP"
        print(f"🔍 Requête de test: '{test_query}'")
        
        # 4. Génération de l'embedding avec OpenAI
        print("🧠 Génération de l'embedding...")
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=test_query
        )
        query_vector = response.data[0].embedding
        print(f"✅ Embedding généré: {len(query_vector)} dimensions")
        
        # 5. Recherche dans Qdrant avec l'embedding
        print(f"🔍 Recherche dans Qdrant (collection: {test_collection})...")
        search_results = qdrant_client.search(
            collection_name=test_collection,
            query_vector=query_vector,
            limit=3  # Limiter à 3 résultats pour le test
        )
        
        # 6. Affichage des résultats
        if not search_results:
            print("⚠️ Aucun résultat trouvé")
            return True  # Considéré comme réussi car la recherche a fonctionné
        
        print(f"✅ {len(search_results)} résultats trouvés:")
        
        for i, result in enumerate(search_results, 1):
            score = result.score
            payload = result.payload
            
            print(f"\n📄 Résultat {i} (score: {score:.4f}):")
            
            # Affichage des champs les plus pertinents
            important_fields = ["title", "summary", "description", "content"]
            displayed_fields = []
            
            for field in important_fields:
                if field in payload and payload[field]:
                    value = payload[field]
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  - {field}: {value}")
                    displayed_fields.append(field)
            
            # Si aucun champ important n'a été trouvé, afficher quelques champs disponibles
            if not displayed_fields:
                sample_fields = list(payload.keys())[:3]
                for field in sample_fields:
                    value = payload[field]
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"  - {field}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de concrétion: {str(e)}")
        traceback.print_exc()
        return False


def main():
    """Fonction principale pour les tests"""
    print_section("DÉMARRAGE DES TESTS")
    
    # Chargement des variables d'environnement
    load_dotenv()
    print("📁 Variables d'environnement chargées depuis .env")
    
    # Test de connexion à Qdrant
    qdrant_success = test_qdrant_connection()
    
    # Test de connexion à OpenAI
    openai_success = test_openai_connection()
    
    # Test du processus complet (concrétion)
    if qdrant_success and openai_success:
        print("\n✅ Les connexions sont établies, test du processus complet...")
        concretion_success = test_full_query_process()
    else:
        concretion_success = False
        print("\n⚠️ Test de concrétion ignoré en raison d'erreurs précédentes")
    
    # Résumé des tests
    print_section("RÉSUMÉ DES TESTS")
    print(f"Connexion à Qdrant: {'✅ Réussie' if qdrant_success else '❌ Échouée'}")
    print(f"Connexion à OpenAI: {'✅ Réussie' if openai_success else '❌ Échouée'}")
    print(f"Test de concrétion: {'✅ Réussi' if concretion_success else '❌ Échoué'}")
    
    # Conseils en cas d'échec
    if not qdrant_success or not openai_success or not concretion_success:
        print("\n🔧 CONSEILS DE DÉPANNAGE:")
        
        if not qdrant_success:
            print("\nPour Qdrant:")
            print("1. Vérifiez que la variable QDRANT_URL est correctement définie")
            print("2. Vérifiez que la variable QDRANT_API_KEY est correctement définie")
            print("3. Assurez-vous que le serveur Qdrant est accessible depuis votre réseau")
            print("4. Vérifiez les logs du serveur Qdrant pour d'éventuelles erreurs")
        
        if not openai_success:
            print("\nPour OpenAI:")
            print("1. Vérifiez que la variable OPENAI_API_KEY est correctement définie")
            print("2. Assurez-vous que votre clé API est valide et active")
            print("3. Vérifiez votre quota d'utilisation sur le tableau de bord OpenAI")
        
        if not concretion_success and qdrant_success and openai_success:
            print("\nPour le test de concrétion:")
            print("1. Vérifiez que la collection Qdrant contient des données")
            print("2. Assurez-vous que les embeddings stockés dans Qdrant sont compatibles avec ceux générés par OpenAI")
            print("3. Vérifiez la dimension des vecteurs dans Qdrant (doit être 1536 pour text-embedding-ada-002)")
            print("4. Essayez une requête différente qui pourrait mieux correspondre aux données de la collection")
    
    return 0 if qdrant_success and openai_success and concretion_success else 1


if __name__ == "__main__":
    sys.exit(main())