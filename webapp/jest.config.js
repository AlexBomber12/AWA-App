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
    "<rootDir>/app/**/*.{ts,tsx}",
    "<rootDir>/components/**/*.{ts,tsx}",
    "<rootDir>/lib/**/*.{ts,tsx}",
    "!<rootDir>/**/index.{ts,tsx}",
    "!<rootDir>/**/stories/**",
    "!<rootDir>/**/types.generated.ts",
  ],
  coverageDirectory: "<rootDir>/coverage",
  coverageThreshold: {
    global: {
      branches: 55,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },
};

module.exports = createJestConfig(customJestConfig);
