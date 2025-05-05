// app/layout.tsx
import '@/app/globals.css';          // <-- importe Tailwind + styles généraux

export const metadata = {
  title: 'ITSHELP Search',
  description: 'Moteur de recherche intelligent Qdrant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-background antialiased">
        {children}
      </body>
    </html>
  );
}
