const nextJest = require("next/jest");

const createJestConfig = nextJest({
  dir: "./",
});

const customJestConfig = {
  testEnvironment: "jest-environment-jsdom",
  coverageProvider: "v8",
  clearMocks: true,
  setupFilesAfterEnv: ["<rootDir>/jest.setup.ts"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
    "^until-async$": "<rootDir>/tests/unit/__mocks__/until-async.ts",
  },
  transformIgnorePatterns: ["/node_modules/(?!((?:until-async)|msw)/)"],
  testMatch: ["<rootDir>/tests/unit/**/*.test.{ts,tsx}"],
  modulePathIgnorePatterns: ["<rootDir>/node_modules_old"],
  collectCoverageFrom: [
    "<rootDir>/components/features/dashboard/**/*.{ts,tsx}",
    "<rootDir>/components/features/roi/**/*.{ts,tsx}",
    "<rootDir>/components/features/sku/**/*.{ts,tsx}",
    "<rootDir>/components/features/returns/**/*.{ts,tsx}",
    "<rootDir>/components/features/ingest/**/*.{ts,tsx}",
    "<rootDir>/components/features/inbox/**/*.{ts,tsx}",
    "<rootDir>/components/data/**/*.{ts,tsx}",
    "<rootDir>/components/layout/**/*.{ts,tsx}",
    "<rootDir>/components/forms/**/*.{ts,tsx}",
    "<rootDir>/lib/api/**/*.{ts,tsx}",
    "<rootDir>/lib/tableState/**/*.{ts,tsx}",
    "<rootDir>/lib/utils.ts",
    "!<rootDir>/**/index.{ts,tsx}",
    "!<rootDir>/**/stories/**",
    "!<rootDir>/**/types.generated.ts",
    "!<rootDir>/**/__tests__/**",
  ],
  coveragePathIgnorePatterns: [
    "<rootDir>/components/data/VirtualizedTable.tsx",
    "<rootDir>/components/features/decision/",
    "<rootDir>/components/features/settings/",
    "<rootDir>/components/providers/",
    "<rootDir>/components/features/roi/types.ts",
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
