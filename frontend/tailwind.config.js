/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#0B0E11',
        panel: '#12161C',
        panel2: '#171C24',
        line: '#232830',
        ink: '#E4E7EB',
        muted: '#6B7280',
        signal: '#00D9A3',
        warn: '#F0A94E',
        danger: '#EF5350',
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        sans: ['Inter', 'ui-sans-serif', 'system-ui'],
      },
      fontSize: {
        '2xs': '0.6875rem',
      },
    },
  },
  plugins: [],
}
