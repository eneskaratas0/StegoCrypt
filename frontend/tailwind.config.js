/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./frontend/index.html', './frontend/static/app.js'],
  theme: {
    extend: {
      colors: {
        bg: '#0F172A',
        ink: '#F8FAFC',
        amber: { DEFAULT: '#F59E0B', light: '#FBBF24' },
        violet: '#8B5CF6',
      },
      fontFamily: {
        display: ['Orbitron', 'sans-serif'],
        body: ['Exo 2', 'sans-serif'],
      },
    },
  },
};
