/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/webhooks/:path*',
        destination: 'http://127.0.0.1:8000/webhooks/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
