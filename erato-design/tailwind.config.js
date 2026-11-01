import theme from './tailwind.theme.js'

/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: theme,
  },
  plugins: [],
}
