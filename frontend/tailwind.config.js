/** @type {import('tailwindcss').Config} */

// RivalBull 牧场设计 token —— 同时提供「扁平命名」(handbook 可粘贴) 与 `bull-` 命名空间
const palette = {
  primary: '#547548',
  'primary-soft': '#afc69a',
  'primary-tint': '#e8efdb',
  'primary-deep': '#3f6036',
  sun: '#f6d78c',
  'sun-soft': '#fff4d9',
  ink: '#34402f',
  'ink-2': '#626b58',
  'ink-3': '#818777',
  line: '#e0e3d3',
  bg: '#faf8ef',
  card: '#FFFFFF',
  ok: '#789b61',
  warn: '#c99a44',
  risk: '#bb7665',
  info: '#759aa8',
}

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ...palette,
        bull: palette,
      },
      borderRadius: {
        card: '16px',
        btn: '12px',
        chip: '999px',
      },
      boxShadow: {
        card: '0 4px 24px rgba(124,152,133,0.08)',
        float: '0 8px 40px rgba(124,152,133,0.14)',
        glow: '0 0 0 4px rgba(124,152,133,0.12)',
      },
      fontFamily: {
        sans: ['Nunito', 'Noto Sans SC', 'PingFang SC', 'sans-serif'],
        serif: ['Noto Serif SC', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'monospace'],
      },
      fontSize: {
        h1: ['28px', { lineHeight: '1.3', fontWeight: '600' }],
        h2: ['22px', { lineHeight: '1.3', fontWeight: '600' }],
        h3: ['18px', { lineHeight: '1.3', fontWeight: '600' }],
        body: ['15px', { lineHeight: '1.7' }],
        aux: ['13px', { lineHeight: '1.6' }],
        tag: ['11px', { lineHeight: '1.4' }],
      },
      spacing: {
        4.5: '18px',
      },
      maxWidth: {
        content: '1440px',
        read: '760px',
      },
      transitionTimingFunction: {
        bull: 'cubic-bezier(.4,0,.2,1)',
      },
      keyframes: {
        breath: { '0%,100%': { opacity: '1' }, '50%': { opacity: '.55' } },
        floatUp: {
          from: { opacity: '0', transform: 'translateY(12px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%,100%': { boxShadow: '0 0 0 0 rgba(124,152,133,.4)' },
          '50%': { boxShadow: '0 0 0 8px rgba(124,152,133,0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        spinSlow: { to: { transform: 'rotate(360deg)' } },
      },
      animation: {
        breath: 'breath 2s ease-in-out infinite',
        floatUp: 'floatUp .4s cubic-bezier(.4,0,.2,1) both',
        glow: 'glow 1.8s ease-in-out infinite',
        shimmer: 'shimmer 1.6s linear infinite',
        'spin-slow': 'spinSlow 8s linear infinite',
      },
    },
  },
  plugins: [],
}
