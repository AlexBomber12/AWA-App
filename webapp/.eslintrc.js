module.exports = {
  root: true,
  parser: "@typescript-eslint/parser",
  plugins: ["@typescript-eslint"],
  extends: ["next/core-web-vitals", "plugin:@typescript-eslint/recommended", "prettier"],
  parserOptions: {
    tsconfigRootDir: __dirname,
  },
  overrides: [
    {
      files: ["tests/**/*.{ts,tsx}", "**/*.test.{ts,tsx}"],
      env: {
        jest: true,
      },
    },
  ],
};
