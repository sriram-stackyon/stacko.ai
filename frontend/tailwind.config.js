/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#eef6ff",
          100: "#daeafe",
          600: "#0f4c81",
          700: "#0c3d66",
        },
      },
    },
  },
  plugins: [],
};
