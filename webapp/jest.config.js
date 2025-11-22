const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  testEnvironment: "jest-environment-jsdom",
  clearMocks: true,
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  testMatch: ["<rootDir>/tests/unit/**/*.test.{ts,tsx}"],
  modulePathIgnorePatterns: ["<rootDir>/node_modules_old"],
  collectCoverageFrom: [
    "<rootDir>/components/**/*.{ts,tsx}",
    "<rootDir>/lib/api/**/*.{ts,tsx}",
    "<rootDir>/lib/permissions.ts",
    "<rootDir>/lib/tableState/**/*.{ts,tsx}",
    "<rootDir>/lib/utils.ts",
    "!<rootDir>/**/index.{ts,tsx}",
    "!<rootDir>/**/stories/**",
    "!<rootDir>/**/types.generated.ts",
    "!<rootDir>/**/__tests__/**",
  ],
  coverageDirectory: "<rootDir>/coverage",
  coverageThreshold: {
    global: {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0,
    },
    "./components/features/dashboard/**": {
      lines: 65,
      branches: 35,
    },
    "./components/features/roi/**": {
      lines: 60,
      branches: 35,
    },
    "./components/features/sku/**": {
      lines: 70,
      branches: 50,
    },
    "./components/features/ingest/**": {
      lines: 55,
      branches: 40,
    },
    "./components/features/returns/**": {
      lines: 75,
      branches: 55,
    },
    "./components/features/inbox/**": {
      lines: 75,
      branches: 55,
    },
    "./lib/tableState/**": {
      lines: 70,
      branches: 50,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
