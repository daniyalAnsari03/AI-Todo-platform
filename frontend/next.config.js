// Task T-043/T-043a • Spec FR-210-213, FR-230-234 • Plan •Frontend plan (rewrite & proxy), •Auth plan (frontend) • Contract tasks-api.md ••Proxy rules
// Deployment note: the rewrite destination is a server-side value (NEXT_PUBLIC_
// vars cannot be used in next.config.js rewrites), so it is read from BACKEND_URL
// at config load time, defaulting to the local backend when unset.
const backendUrl = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(
  /\/+$/,
  "",
);

const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:userId/chat",
        destination: `${backendUrl}/api/:userId/chat`,
      },
      {
        source: "/api/:userId/chatkit",
        destination: `${backendUrl}/api/:userId/chatkit`,
      },
      {
        source: "/api/:userId/tasks",
        destination: `${backendUrl}/api/:userId/tasks`,
      },
      {
        source: "/api/:userId/tasks/:path*",
        destination: `${backendUrl}/api/:userId/tasks/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
