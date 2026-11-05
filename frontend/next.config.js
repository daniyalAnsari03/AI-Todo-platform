// Task T-043/T-043a · Spec FR-210–213, FR-230–234 · Plan §Frontend plan (rewrite & proxy), §Auth plan (frontend) · Contract tasks-api.md §Proxy rules
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:userId/chat",
        destination: "http://127.0.0.1:8000/api/:userId/chat",
      },
      {
        source: "/api/:userId/chatkit",
        destination: "http://127.0.0.1:8000/api/:userId/chatkit",
      },
      {
        source: "/api/:userId/tasks",
        destination: "http://127.0.0.1:8000/api/:userId/tasks",
      },
      {
        source: "/api/:userId/tasks/:path*",
        destination: "http://127.0.0.1:8000/api/:userId/tasks/:path*",
      },
    ];
  },
};

module.exports = nextConfig;
