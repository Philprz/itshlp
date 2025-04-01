# Guide de déploiement sur Render

Ce document explique comment déployer l'application Qdrant Web sur Render.

## Prérequis

- Un compte Render (https://render.com)
- Accès à un serveur Qdrant avec les collections appropriées
- La clé API Qdrant pour l'authentification

## Étapes de déploiement

1. Connectez-vous à votre compte Render

2. Créez un nouveau service Web :
   - Cliquez sur "New" puis "Web Service"
   - Connectez votre dépôt Git contenant le code de l'application
   - Sélectionnez la branche à déployer

3. Configurez le service :
   - **Nom** : itshlp
   - **Environnement** : Node
   - **Commande de build** : `npm install && npm run build`
   - **Commande de démarrage** : `npm start`

4. Configurez les variables d'environnement :
   - `NODE_ENV` : production
   - `QDRANT_URL` : URL de votre serveur Qdrant
   - `QDRANT_API_KEY` : Votre clé API Qdrant (marquez-la comme secrète)
   - `QDRANT_COLLECTION_ZENDESK` : ZENDESK
   - `QDRANT_COLLECTION_JIRA` : JIRA
   - `QDRANT_COLLECTION_CONFLUENCE` : CONFLUENCE
   - `QDRANT_COLLECTION_NETSUITE` : NETSUITE
   - `QDRANT_COLLECTION_NETSUITE_DUMMIES` : NETSUITE_DUMMIES
   - `QDRANT_COLLECTION_SAP` : SAP

5. Cliquez sur "Create Web Service" pour lancer le déploiement


## Après le déploiement

Une fois le déploiement terminé, Render vous fournira une URL pour accéder à votre application (généralement sous la forme `https://itshlp.onrender.com`).

## Dépannage

- Si vous rencontrez des erreurs liées à Qdrant, vérifiez que les variables d'environnement sont correctement configurées
- Pour les problèmes de build, consultez les logs de déploiement dans l'interface Render
- Si l'application se charge mais que les recherches échouent, vérifiez que votre serveur Qdrant est accessible depuis Render
