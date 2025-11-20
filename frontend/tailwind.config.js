/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e9ff',
          200: '#c7d6fe',
          300: '#a5b8fc',
          400: '#8695f8',
          500: '#6c72f0',
          600: '#5a56e4',
          700: '#4b45c9',
          800: '#3d3aa3',
          900: '#363682',
        },
      },
    },
  },
  plugins: [],
}
