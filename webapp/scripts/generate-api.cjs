#!/usr/bin/env node

const { spawn } = require("node:child_process");
const path = require("node:path");

const resolveSchemaUrl = () => {
  if (process.env.OPENAPI_SCHEMA_URL) {
    return process.env.OPENAPI_SCHEMA_URL;
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_URL;
  if (baseUrl) {
    try {
      return new URL("/openapi.json", baseUrl).toString();
    } catch (error) {
      console.warn("Invalid NEXT_PUBLIC_API_URL provided, falling back to localhost:", error);
    }
  }

  return "http://localhost:8000/openapi.json";
};

const schemaUrl = resolveSchemaUrl();
const outputPath = path.resolve(__dirname, "..", "lib/api/types.generated.ts");

const cliPath = (() => {
  try {
    return require.resolve("openapi-typescript/bin/cli.js");
  } catch (error) {
    console.error("Cannot find openapi-typescript. Did you run npm install?");
    throw error;
  }
})();

const child = spawn(
  process.execPath,
  [cliPath, schemaUrl, "--output", outputPath],
  {
    stdio: "inherit",
  }
);

child.on("error", (error) => {
  console.error("Failed to run openapi-typescript:", error);
  process.exit(1);
});

child.on("close", (code) => {
  if (code !== 0) {
    console.error(`openapi-typescript exited with code ${code}.`);
    process.exit(code ?? 1);
  }
});
