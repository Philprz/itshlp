# Solution de déploiement Python pour Render

## Pourquoi déployer en Python ?

Après analyse de votre projet, il est clair que votre application est principalement basée sur Python avec une interface web Next.js. Puisque le code Python (main.py, query_system.py) est utilisé comme backend API que l'interface Next.js appelle, un déploiement Python est plus approprié pour les raisons suivantes :

1. La logique métier principale est en Python
2. Les interactions avec Qdrant sont gérées par le code Python
3. Le traitement des requêtes et le formatage des réponses sont implémentés en Python

## Configuration de déploiement Python

J'ai préparé les fichiers nécessaires pour un déploiement Python sur Render :

### 1. requirements.txt

Ce fichier liste toutes les dépendances Python nécessaires :

```
qdrant-client==0.0.1
python-dotenv==1.0.0
numpy==1.24.3
fastapi==0.104.1
uvicorn==0.23.2
pydantic==2.4.2
python-multipart==0.0.6
```

### 2. app.py

J'ai créé un fichier app.py qui expose une API FastAPI pour votre système Qdrant. Cette API :
- Expose un endpoint `/api/search` qui correspond à la fonctionnalité de votre route.ts
- Utilise votre classe QdrantSystem existante de main.py
- Gère les requêtes CORS pour permettre les appels depuis votre frontend Next.js
- Démarre un serveur Uvicorn sur le port spécifié par Render

### 3. render.yaml.python

J'ai créé une version Python de votre fichier render.yaml :

```yaml
# Fichier de configuration pour le déploiement sur Render
# Version Python pour l'application Qdrant Web

services:
  - type: web
    name: qdrant-web-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python app.py
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: QDRANT_URL
        value: https://b361537d-20a3-4a84-b96f-9efb19837c15.us-east4-0.gcp.cloud.qdrant.io
      - key: QDRANT_COLLECTION_ZENDESK
        value: ZENDESK
      - key: QDRANT_COLLECTION_JIRA
        value: JIRA
      - key: QDRANT_COLLECTION_CONFLUENCE
        value: CONFLUENCE
      - key: QDRANT_COLLECTION_NETSUITE
        value: NETSUITE
      - key: QDRANT_COLLECTION_NETSUITE_DUMMIES
        value: NETSUITE_DUMMIES
      - key: QDRANT_COLLECTION_SAP
        value: SAP
      - key: QDRANT_API_KEY
        sync: false
    healthCheckPath: /
    autoDeploy: true
```

## Étapes pour déployer sur Render

1. **Renommez le fichier render.yaml.python en render.yaml** :
   ```
   mv render.yaml.python render.yaml
   ```

2. **Assurez-vous que tous les fichiers sont à la racine de votre projet** :
   - main.py
   - query_system.py
   - app.py
   - requirements.txt
   - render.yaml
   - ListeClients.csv
   - .env (pour le développement local)

3. **Poussez ces modifications vers votre dépôt Git**

4. **Déployez sur Render** :
   - Si vous utilisez le déploiement manuel : Créez un nouveau service Web, sélectionnez Python comme environnement
   - Si vous utilisez le Blueprint : Render détectera automatiquement le fichier render.yaml et configurera le service

5. **Configurez la variable d'environnement QDRANT_API_KEY** dans l'interface Render

## Adaptation du frontend Next.js

Votre frontend Next.js devra être adapté pour appeler l'API Python déployée. Vous avez deux options :

1. **Déployer le frontend séparément** :
   - Créez un nouveau service Render pour le frontend Next.js
   - Configurez-le pour appeler l'URL de votre API Python

2. **Servir le frontend statique depuis l'API Python** :
   - Construisez votre application Next.js en statique (`next build && next export`)
   - Ajoutez le code nécessaire à app.py pour servir ces fichiers statiques

## Notes importantes

1. **Version de qdrant-client** : J'ai spécifié la version 0.0.1 de qdrant-client car c'est la seule version disponible dans PyPI. Si votre code nécessite une version plus récente, vous devrez peut-être adapter votre code.

2. **Port** : L'application utilise la variable d'environnement PORT fournie par Render, ou par défaut le port 8000.

3. **CORS** : La configuration CORS actuelle permet les requêtes de n'importe quelle origine. En production, vous devriez restreindre cela à l'origine exacte de votre frontend.

4. **Sécurité** : Assurez-vous que votre API est correctement sécurisée, surtout si elle expose des données sensibles.

5. **Logs** : Render fournit des logs pour votre application, ce qui vous permettra de déboguer les problèmes éventuels.
