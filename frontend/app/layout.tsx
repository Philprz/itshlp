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
