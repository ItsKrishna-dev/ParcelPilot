import type { Config } from 'tailwindcss';

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          950: '#080c14',
          900: '#0d1322',
          850: '#11192e',
          800: '#18223c',
          700: '#223052',
          600: '#314470',
        },
        brand: {
          blue: '#3b82f6',
          cyan: '#06b6d4',
          emerald: '#10b981',
          amber: '#f59e0b',
          red: '#ef4444',
          violet: '#8b5cf6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        'glass-sm': '0 4px 16px 0 rgba(0, 0, 0, 0.25)',
        'glass-md': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glow-blue': '0 0 20px -5px rgba(59, 130, 246, 0.3)',
        'glow-violet': '0 0 20px -5px rgba(139, 92, 246, 0.3)',
        'glow-emerald': '0 0 20px -5px rgba(16, 185, 129, 0.3)',
      },
    },
  },
  plugins: [],
} satisfies Config;
