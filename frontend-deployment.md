# Déploiement de l'Interface Utilisateur Next.js

## Vue d'ensemble

Votre application se compose de deux parties principales :

1. **Backend Python (API)** - Déjà déployé sur Render
   - Fournit l'API pour interroger les collections Qdrant
   - Point de terminaison principal : `/api/search`

2. **Frontend Next.js** - À déployer
   - Interface utilisateur conviviale pour interagir avec l'API
   - Formulaire de recherche avec filtres et options de format
   - Affichage des résultats formatés

## Solution de déploiement

Pour obtenir une interface utilisateur complète plutôt qu'une simple API JSON, nous allons déployer votre application Next.js existante (page.tsx et route.ts) en tant que service distinct qui communiquera avec l'API Python déjà déployée.

### Étapes de déploiement

1. **Créer un nouveau projet Next.js**

```bash
mkdir qdrant-frontend
cd qdrant-frontend
npm init -y
npm install next react react-dom @qdrant/js-client-rest luxon
npm install -D typescript @types/node @types/react @types/luxon
npx create-next-app@latest .
```

2. **Copier les fichiers existants**

Créez la structure de répertoires suivante et copiez les fichiers :

```
qdrant-frontend/
├── .env.local
├── package.json
├── next.config.js
├── app/
│   ├── page.tsx       # Votre fichier page.tsx existant
│   ├── globals.css    # Votre fichier globals.css existant
│   ├── layout.tsx     # Fichier de mise en page Next.js
│   └── api/
│       └── search/
│           └── route.ts  # Fichier route.ts modifié
```

3. **Modifier le fichier route.ts**

Le fichier route.ts doit être modifié pour appeler l'API Python déployée au lieu d'interagir directement avec Qdrant :

```typescript
// app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';

// URL de l'API Python déployée sur Render
const API_URL = process.env.API_URL || 'https://itship.onrender.com';

export async function POST(request: NextRequest) {
  try {
    const requestData = await request.json();
    
    // Transmettre la requête à l'API Python
    const response = await fetch(`${API_URL}/api/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestData),
    });
    
    const data = await response.json();
    
    // Retourner la réponse de l'API Python
    return NextResponse.json(data);
  } catch (error: any) {
    console.error('Erreur lors du traitement de la requête:', error);
    return NextResponse.json(
      { error: error.message || 'Une erreur est survenue lors du traitement de la requête' },
      { status: 500 }
    );
  }
}
```

4. **Créer un fichier .env.local**

```
API_URL=https://itship.onrender.com
```

5. **Créer un fichier next.config.js**

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
```

6. **Créer un fichier layout.tsx**

```tsx
// app/layout.tsx
import './globals.css';

export const metadata = {
  title: 'IT SPIRIT - Système d\'Information Qdrant',
  description: 'Recherchez des informations sur les clients et les systèmes ERP (SAP et NetSuite)',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body>{children}</body>
    </html>
  );
}
```

7. **Mettre à jour le fichier package.json**

```json
{
  "name": "qdrant-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint"
  },
  "dependencies": {
    "@qdrant/js-client-rest": "^1.6.0",
    "luxon": "^3.4.4",
    "next": "14.1.0",
    "react": "^18",
    "react-dom": "^18",
    "lucide-react": "^0.323.0"
  },
  "devDependencies": {
    "@types/luxon": "^3.4.2",
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "autoprefixer": "^10.0.1",
    "eslint": "^8",
    "eslint-config-next": "14.1.0",
    "postcss": "^8",
    "tailwindcss": "^3.3.0",
    "typescript": "^5"
  }
}
```

8. **Déployer sur Render**

- Créez un nouveau service Web sur Render
- Sélectionnez Node.js comme environnement
- Configurez les variables d'environnement :
  - `API_URL` : URL de votre API Python déployée (https://itship.onrender.com)
- Commande de build : `npm install && npm run build`
- Commande de démarrage : `npm start`

## Résultat final

Après le déploiement, vous aurez :

1. Une API Python déployée sur Render (déjà fait)
2. Une interface utilisateur Next.js déployée sur Render qui communique avec l'API Python

L'utilisateur accédera à l'interface utilisateur Next.js, qui lui permettra d'effectuer des recherches et d'afficher les résultats dans un format convivial, tout en utilisant l'API Python en arrière-plan pour interroger les collections Qdrant.

## Avantages de cette approche

1. **Séparation des préoccupations** : Le backend Python se concentre sur l'interaction avec Qdrant, tandis que le frontend Next.js se concentre sur l'interface utilisateur.
2. **Évolutivité** : Les deux services peuvent évoluer indépendamment.
3. **Performance** : Le frontend Next.js est optimisé pour le rendu côté client, offrant une expérience utilisateur fluide.
4. **Réutilisation du code existant** : Nous utilisons les fichiers page.tsx et route.ts que vous avez déjà développés.
