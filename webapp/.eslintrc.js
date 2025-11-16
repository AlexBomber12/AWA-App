module.exports = {
  root: true,
  extends: ["next/core-web-vitals", "next/typescript", "prettier"],
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
