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
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7ccbfd',
          400: '#36b2fa',
          500: '#2E75B6',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
        navy: {
          50: '#f2f5f8',
          100: '#e1e8f0',
          200: '#c4d3e3',
          300: '#9ab5cd',
          400: '#6f93b3',
          500: '#50789c',
          600: '#3e6080',
          700: '#334e68',
          800: '#2c4256',
          900: '#1B3A5C',
        }
      }
    },
  },
  plugins: [],
}
