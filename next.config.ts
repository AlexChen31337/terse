import type { NextConfig } from 'next';

/**
 * Next.js configuration
 * Generated 2026-03-25 — aligned with workspace stack:
 *   React 19, TypeScript, Tailwind CSS v4, Zustand, Zod, Firebase, lucide-react
 */
const nextConfig: NextConfig = {
  // ─── Output & Runtime ────────────────────────────────────────────────────────
  output: 'standalone', // Self-contained output for Docker / serverless deploys
  reactStrictMode: true, // Enable React strict mode for surfacing potential issues
  poweredByHeader: false, // Remove "X-Powered-By: Next.js" response header

  // ─── TypeScript & ESLint ─────────────────────────────────────────────────────
  typescript: {
    // Set to true only in CI to surface type errors as build failures
    ignoreBuildErrors: false,
  },
  eslint: {
    ignoreDuringBuilds: false,
    dirs: ['src', 'app', 'pages', 'components', 'lib', 'hooks', 'utils'],
  },

  // ─── Compiler (SWC) ──────────────────────────────────────────────────────────
  compiler: {
    // Enable styled-components support (display names + SSR class name stability)
    styledComponents: {
      displayName: true,
      ssr: true,
      fileName: true,
      minify: process.env.NODE_ENV === 'production',
    },
    // Strip console.log calls in production (keep warn/error)
    removeConsole:
      process.env.NODE_ENV === 'production'
        ? { exclude: ['warn', 'error'] }
        : false,
    // Emotion support (uncomment if using @emotion/react instead of styled-components)
    // emotion: {
    //   autoLabel: 'dev-only',
    //   labelFormat: '[local]',
    //   sourceMap: true,
    //   importMap: {},
    // },
  },

  // ─── Experimental Features ───────────────────────────────────────────────────
  experimental: {
    // React compiler (opt-in — requires `babel-plugin-react-compiler`)
    // reactCompiler: true,

    // Partial pre-rendering: blend static shell + streaming dynamic content
    ppr: false, // Set to 'incremental' to opt pages in via `export const experimental_ppr = true`

    // Typed routes — type-safe `href` in <Link> and `useRouter`
    typedRoutes: true,

    // Server Actions are stable in Next.js 14+; keep flag for older compatibility
    serverActions: {
      bodySizeLimit: '2mb',
      allowedOrigins: process.env.ALLOWED_ORIGINS?.split(',') ?? [],
    },

    // Optimise package imports (tree-shake icon/component libraries)
    optimizePackageImports: [
      'lucide-react',
      'zustand',
      '@radix-ui/react-icons',
      'date-fns',
      'lodash',
      'lodash-es',
    ],

    // Turbopack (stable in Next.js 15) — replaces webpack for dev
    turbo: {
      rules: {
        '*.svg': {
          loaders: ['@svgr/webpack'],
          as: '*.js',
        },
      },
    },

    // Parallel route segment fetching
    parallelServerBuildTraces: true,
    parallelServerCompiles: true,

    // CSS in Server Components (experimental)
    cssChunking: 'strict',
  },

  // ─── Image Optimisation ───────────────────────────────────────────────────────
  images: {
    formats: ['image/avif', 'image/webp'],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    minimumCacheTTL: 60 * 60 * 24 * 30, // 30 days
    remotePatterns: [
      // Firebase Storage
      {
        protocol: 'https',
        hostname: 'firebasestorage.googleapis.com',
        pathname: '/v0/b/**',
      },
      // Cloudflare Images / R2
      {
        protocol: 'https',
        hostname: '*.cloudflare.com',
      },
      // Development / localhost images
      ...(process.env.NODE_ENV === 'development'
        ? [{ protocol: 'http' as const, hostname: 'localhost' }]
        : []),
    ],
  },

  // ─── Internationalization ─────────────────────────────────────────────────────
  // i18n: {
  //   locales: ['en', 'zh'],
  //   defaultLocale: 'en',
  // },

  // ─── Headers ─────────────────────────────────────────────────────────────────
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=63072000; includeSubDomains; preload',
          },
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              "script-src 'self' 'unsafe-eval' 'unsafe-inline' https://apis.google.com",
              "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
              "font-src 'self' https://fonts.gstatic.com",
              "img-src 'self' data: blob: https:",
              "connect-src 'self' https://*.firebaseio.com https://*.googleapis.com wss://*.firebaseio.com",
              "frame-src 'none'",
            ].join('; '),
          },
        ],
      },
      // Cache static assets aggressively
      {
        source: '/static/(.*)',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable',
          },
        ],
      },
    ];
  },

  // ─── Redirects ────────────────────────────────────────────────────────────────
  async redirects() {
    return [
      // Example: redirect legacy routes
      // { source: '/old-path', destination: '/new-path', permanent: true },
    ];
  },

  // ─── Rewrites ────────────────────────────────────────────────────────────────
  async rewrites() {
    return {
      beforeFiles: [],
      afterFiles: [
        // Proxy API calls to avoid CORS in development
        ...(process.env.NODE_ENV === 'development' && process.env.API_URL
          ? [
              {
                source: '/api/:path*',
                destination: `${process.env.API_URL}/api/:path*`,
              },
            ]
          : []),
      ],
      fallback: [],
    };
  },

  // ─── Webpack customisation (fallback when Turbopack is not used) ──────────────
  webpack(config, { isServer, dev }) {
    // SVG as React components
    config.module.rules.push({
      test: /\.svg$/i,
      use: [
        {
          loader: '@svgr/webpack',
          options: { typescript: true, dimensions: false },
        },
      ],
    });

    // Provide Node.js polyfills for Firebase on the client
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
        net: false,
        tls: false,
        crypto: require.resolve('crypto-browserify'),
        stream: require.resolve('stream-browserify'),
        buffer: require.resolve('buffer'),
      };
    }

    // Bundle analyser (run: ANALYZE=true next build)
    if (process.env.ANALYZE === 'true') {
      const { BundleAnalyzerPlugin } =
        // eslint-disable-next-line @typescript-eslint/no-require-imports
        require('webpack-bundle-analyzer');
      config.plugins.push(
        new BundleAnalyzerPlugin({
          analyzerMode: 'static',
          reportFilename: isServer
            ? '../analyze/server.html'
            : './analyze/client.html',
          openAnalyzer: false,
        }),
      );
    }

    return config;
  },

  // ─── Environment variables exposed to the browser ────────────────────────────
  // Prefer NEXT_PUBLIC_ prefix; list here for documentation purposes only.
  // env: {
  //   NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version,
  // },
};

export default nextConfig;
