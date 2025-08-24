module.exports = {
  "src/**/*.{ts,tsx}": (filenames) => [
    `eslint --fix ${filenames.join(' ')}`,
    "tsc -p tsconfig.json --noEmit",
  ],
};
