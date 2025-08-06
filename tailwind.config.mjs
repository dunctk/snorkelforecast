/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./conditions/**/*.{html,py}",
    "./snorkelforecast/**/*.{html,py}",
    "./static/**/*.html",
  ],
  safelist: [
    'bg-sky-50',
    'min-h-screen',
    'flex',
    'flex-col',
    'items-center',
    'p-4',
    'text-2xl',
    'font-bold',
    'mb-4',
    'grid',
    'grid-cols-6',
    'sm:grid-cols-12',
    'gap-1',
    'text-xs',
    'p-2',
    'rounded',
    'bg-emerald-400',
    'bg-gray-300',
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
