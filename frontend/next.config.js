/** @type {import('next').NextConfig} */
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  compress: true,
  poweredByHeader: false,
  output: 'export',  // Ajoutez cette ligne pour l'export statique
  // Commentez la section rewrites car nous n'en aurons plus besoin
  /*
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.API_URL || 'https://itshlp.onrender.com'}/api/:path*`,
      },
    ];
  },
  */
};

module.exports = withBundleAnalyzer(nextConfig);
