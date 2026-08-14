/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f4f6f9',
          100: '#e5eaef',
          200: '#c5d0de',
          300: '#97abc2',
          400: '#6481a3',
          500: '#1a365d', // primary brand accent
          600: '#173053',
          700: '#142947',
          800: '#10213b',
          900: '#0e1c32',
          950: '#091220',
        },
        paper: {
          DEFAULT: '#fcf9f8',
          dim: '#f4f1ef',
          dark: '#1c1917',
        },
        ink: {
          muted: '#625b57',
          DEFAULT: '#1c1917', // warm black / carbon ink
          dark: '#0c0a09',
        },
        divider: {
          DEFAULT: '#e5e2da',
          warm: '#e5e2da',
        },
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['"Hanken Grotesk"', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['"Geist Mono"', 'monospace'],
      },
      borderRadius: {
        none: '0px',
        xs: '1px',
        sm: '2px',
        DEFAULT: '2px',
        md: '4px',
        lg: '4px',
        xl: '4px',
      },
    },
  },
  plugins: [],
}
