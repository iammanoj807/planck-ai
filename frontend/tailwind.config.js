/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                pplx: {
                    dark: '#191A1A',     // Main background
                    card: '#202222',     // Secondary/Card background
                    hover: '#2C2D2D',    // Hover state
                    border: '#2E3030',   // Borders
                    text: '#E8E8E8',     // Main text
                    muted: '#8C8C8C',    // Muted text
                    accent: '#309aa5',   // Teal accent (User requested)
                }
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
                serif: ['"Instrument Serif"', 'serif'],
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-out',
                'slide-up': 'slideUp 0.5s ease-out',
                'pulse-slow': 'pulse 3s infinite',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0', transform: 'translateY(10px)' },
                    '100%': { opacity: '1', transform: 'translateY(0)' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(100%)' },
                    '100%': { transform: 'translateY(0)' },
                }
            }
        },
    },
    plugins: [],
}
