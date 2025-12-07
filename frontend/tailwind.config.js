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
          50: '#fef3f2',
          100: '#fde6e4',
          200: '#fbd0cc',
          300: '#f8aea8',
          400: '#f27f76',
          500: '#e85a4f',
          600: '#d43d31',
          700: '#b23125',
          800: '#932c22',
          900: '#7a2a22',
          950: '#42120e',
        },
        dark: {
          50: '#f6f6f7',
          100: '#e2e3e5',
          200: '#c4c6cb',
          300: '#9fa2a9',
          400: '#7b7f87',
          500: '#60636c',
          600: '#4c4e56',
          700: '#3f4046',
          800: '#35363a',
          900: '#1a1a1e',
          950: '#0d0d0f',
        },
        accent: {
          gold: '#f8b500',
          teal: '#2dd4bf',
          purple: '#a855f7',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Outfit', 'system-ui', 'sans-serif'],
      },
      animation: {
        'swipe-left': 'swipeLeft 0.3s ease-out forwards',
        'swipe-right': 'swipeRight 0.3s ease-out forwards',
        'swipe-up': 'swipeUp 0.3s ease-out forwards',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        swipeLeft: {
          '0%': { transform: 'translateX(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'translateX(-150%) rotate(-20deg)', opacity: '0' },
        },
        swipeRight: {
          '0%': { transform: 'translateX(0) rotate(0deg)', opacity: '1' },
          '100%': { transform: 'translateX(150%) rotate(20deg)', opacity: '0' },
        },
        swipeUp: {
          '0%': { transform: 'translateY(0)', opacity: '1' },
          '100%': { transform: 'translateY(-150%)', opacity: '0' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
