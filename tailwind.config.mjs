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
    // Theme variants
    'ui-day',
    'ui-twilight',
    'ui-night',
    'ui-day:bg-white',
    'ui-twilight:bg-indigo-50',
    'ui-night:bg-gray-800',
    'ui-night:text-white',
    'ui-night:text-gray-300',
    'ui-night:bg-gray-700',
    'ui-night:border-gray-700',
    'ui-night:hover:bg-gray-700',
    'ui-night:text-gray-400',
    'ui-night:bg-blue-900/30',
    'ui-night:bg-blue-900/50',
    'ui-night:text-blue-300',
    'ui-night:border-blue-800',
    'ui-night:bg-gray-900',
    'ui-night:text-gray-500',
    'ui-night:placeholder-gray-400',
    'ui-night:focus:ring-blue-400',
    'ui-night:bg-gray-800/90',
    'ui-night:bg-gray-800/80',
    'ui-night:border-gray-600/50',
    'ui-night:text-gray-100',
    'ui-night:bg-blue-700',
    'ui-night:hover:bg-blue-800',
    'ui-night:ring-blue-500/20',
    'ui-night:border-blue-500/50',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    function({ addVariant }) {
      addVariant('ui-day', '.ui-day &');
      addVariant('ui-twilight', '.ui-twilight &');
      addVariant('ui-night', '.ui-night &');
    }
  ],
}
