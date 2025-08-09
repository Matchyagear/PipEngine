/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./public/index.html"
  ],
  theme: {
    extend: {
      colors: {
        carbon: {
          900: '#0b0f14',
          800: '#11161d',
          700: '#171e27',
          600: '#1f2a36',
        },
        accent: {
          blue: '#33a2ff',
          purple: '#7c4dff',
          cyan: '#00e5ff'
        }
      },
      boxShadow: {
        glossy: '0 2px 10px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.04)',
      },
      backgroundImage: {
        'carbon-fiber': "radial-gradient(circle at 1px 1px, rgba(255,255,255,0.04) 1px, transparent 0), radial-gradient(circle at 3px 3px, rgba(255,255,255,0.02) 2px, transparent 0)",
      },
      backgroundSize: {
        'carbon-fiber': '6px 6px, 6px 6px',
      }
    },
  },
  plugins: [],
};