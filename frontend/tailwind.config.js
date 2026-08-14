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
          dark: '#1c1917',
        },
        ink: {
          muted: '#625b57',
          DEFAULT: '#1c1917', // warm black / deep near-black ink
          dark: '#0c0a09',
        },
      },
      fontFamily: {
        serif: ['"Source Serif 4"', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        none: '0px',
        xs: '1px',
        sm: '2px',
        DEFAULT: '3px',
        md: '4px',
        lg: '6px',
        xl: '8px',
      },
    },
  },
  plugins: [],
}
