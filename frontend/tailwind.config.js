/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: 'var(--canvas)',
          subtle: 'var(--canvas-subtle)',
        },
        ink: 'var(--ink)',
        text: {
          body: 'var(--text-body)',
          muted: 'var(--text-muted)',
        },
        brand: {
          DEFAULT: 'var(--brand)',
          hover: 'var(--brand-hover)',
          active: 'var(--brand-active)',
          soft: 'var(--brand-soft)',
        },
        link: 'var(--link)',
        border: {
          DEFAULT: 'var(--border)',
          subtle: 'var(--border-subtle)',
          input: 'var(--input-border)',
        },
        gold: {
          DEFAULT: 'var(--gold)',
          text: 'var(--gold-text)',
          decor: 'var(--gold-decor)',
        },
        success: {
          DEFAULT: 'var(--success)',
          bg: 'var(--success-bg)',
          text: 'var(--success-text)',
        },
        danger: {
          DEFAULT: 'var(--danger)',
          bg: 'var(--danger-bg)',
          text: 'var(--danger-text)',
        },
        warning: {
          DEFAULT: 'var(--warning)',
          bg: 'var(--warning-bg)',
          text: 'var(--warning-text)',
        },
        info: {
          DEFAULT: 'var(--info)',
          bg: 'var(--info-bg)',
          text: 'var(--info-text)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      fontSize: {
        '2xs': ['0.65rem', { lineHeight: '0.85rem' }],
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(8, 28, 52, 0.06), 0 1px 2px 0 rgba(8, 28, 52, 0.04)',
        'card-hover': '0 4px 6px -1px rgba(8, 28, 52, 0.08), 0 2px 4px -1px rgba(8, 28, 52, 0.04)',
        'nav': '0 1px 3px 0 rgba(8, 28, 52, 0.08)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
      },
    },
  },
  plugins: [],
}
