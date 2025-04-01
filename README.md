# Programme Client Qdrant pour IT SPIRIT

Ce programme permet d'interroger les collections Qdrant contenant des informations sur les clients IT SPIRIT et les systèmes ERP (SAP et NetSuite).

## Fonctionnalités

- Connexion à Qdrant avec les informations d'authentification du fichier .env
- Interrogation des six collections Qdrant :
  - ZENDESK : Tickets historiques des clients, principalement SAP
  - JIRA : Tickets et projets depuis avril 2024
  - CONFLUENCE : Informations clients, contrats, documentation, personnalisations ERP
  - SAP : Documents de procédure du site web SAP
  - NETSUITE : Contenu du site d'aide NetSuite
  - NETSUITE_DUMMIES : Contenu du livre "NetSuite for Dummies" (2015)
- Priorisation des collections selon le contexte :
  - Pour les informations spécifiques à un client : JIRA → CONFLUENCE → ZENDESK
  - Pour les informations générales sur SAP : SAP → JIRA → CONFLUENCE → ZENDESK
  - Pour les informations générales sur NetSuite : NETSUITE → NETSUITE_DUMMIES → JIRA → CONFLUENCE → ZENDESK
- Formatage des réponses selon trois formats :
  - Summary : Aperçu bref (format par défaut)
  - Detail : Explication complète
  - Guide : Instructions étape par étape
- Filtrage par date pour les informations récentes (moins de 6 mois)
- Limitation du nombre de résultats (par défaut 5 tickets)
- Gestion des requêtes ambiguës et demandes de clarification

## Prérequis

- Python 3.10 ou supérieur
- Bibliothèques Python :
  - qdrant-client
  - python-dotenv
  - numpy

## Installation

1. Clonez ce dépôt ou téléchargez les fichiers
2. Installez les dépendances :

```bash
pip install qdrant-client python-dotenv numpy
```

3. Configurez le fichier .env avec vos informations de connexion à Qdrant :

```
QDRANT_URL=votre_url_qdrant
QDRANT_API_KEY=votre_api_key
QDRANT_COLLECTION_ZENDESK=ZENDESK
QDRANT_COLLECTION_JIRA=JIRA
QDRANT_COLLECTION_CONFLUENCE=CONFLUENCE
QDRANT_COLLECTION_NETSUITE=NETSUITE
QDRANT_COLLECTION_NETSUITE_DUMMIES=NETSUITE_DUMMIES
QDRANT_COLLECTION_SAP=SAP
```

## Structure du projet

- `main.py` : Programme principal contenant la classe QdrantSystem
- `test.py` : Script de test pour vérifier le bon fonctionnement du programme
- `.env` : Fichier de configuration contenant les informations de connexion à Qdrant

## Utilisation

### Utilisation basique

```python
from main import QdrantSystem

# Initialisation du système
clients_file = "chemin/vers/ListeClients.csv"
system = QdrantSystem(clients_file)

# Exemple de requête
query_result = system.process_query(
    query_text="Problèmes de connexion",
    client_name="AZERGO",
    recent_only=True,
    limit=5,
    format_type="Summary"
)

# Affichage des résultats
print(query_result)
```

### Exemples de requêtes

1. Recherche pour un client spécifique :

```python
result = system.process_query(
    query_text="Problèmes de connexion",
    client_name="AZERGO",
    recent_only=True,
    limit=5,
    format_type="Summary"
)
```

2. Recherche pour un ERP spécifique :

```python
result = system.process_query(
    query_text="Configuration comptabilité",
    erp="NetSuite",
    recent_only=False,
    limit=5,
    format_type="Detail"
)
```

3. Recherche avec format Guide :

```python
result = system.process_query(
    query_text="Installation module",
    client_name="AZERGO",
    erp="SAP",
    recent_only=True,
    limit=5,
    format_type="Guide"
)
```

## Limitations actuelles et améliorations futures

1. **Embeddings** : Le programme utilise actuellement des vecteurs aléatoires pour simuler les embeddings. Dans une implémentation réelle, il faudrait utiliser un modèle d'embedding comme OpenAI ou SentenceTransformers.

2. **Filtrage par date** : Le filtrage par date est actuellement désactivé car il cause des erreurs avec les données de test. Dans une implémentation réelle, il faudrait s'assurer que les champs de date sont correctement formatés dans Qdrant.

3. **Gestion des erreurs** : La gestion des erreurs pourrait être améliorée pour fournir des messages plus précis et des solutions alternatives en cas d'échec.

4. **Interface utilisateur** : Une interface utilisateur (web ou CLI) pourrait être ajoutée pour faciliter l'utilisation du programme.

## Exécution des tests

Pour exécuter les tests et vérifier le bon fonctionnement du programme :

```bash
python test.py
```

Les tests vérifient :
- La connexion à Qdrant
- La récupération des informations client
- La priorisation des collections
- Le formatage des réponses
- La recherche dans les collections

## Licence

Ce programme est fourni à IT SPIRIT pour un usage interne uniquement.
