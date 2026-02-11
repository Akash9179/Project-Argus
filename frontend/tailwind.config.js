/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        argus: {
          primary: '#08090A',
          secondary: '#111214',
          tertiary: '#1A1C1F',
          accent: '#00A3FF',
          'accent-dim': '#00A3FF33',
          'accent-glow': '#00A3FF66',
          neutral: '#6B7280',
          'neutral-light': '#9CA3AF',
          light: '#F8FAFC',
          surface: '#0D0E10',
          border: '#1E2025',
          'border-light': '#2A2D33',
        },
        alert: {
          critical: '#FF3B30',
          warning: '#FF9500',
          info: '#00A3FF',
          success: '#30D158',
        },
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'SF Mono', 'Consolas', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xxs': '0.625rem',  // 10px
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan': 'scan 4s linear infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
