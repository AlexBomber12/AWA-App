#!/usr/bin/env node

import { spawn } from "node:child_process";
import { setTimeout as delay } from "node:timers/promises";

import lighthouse from "lighthouse";
import { launch } from "chrome-launcher";

const BASE_URL = process.env.LIGHTHOUSE_URL ?? "http://127.0.0.1:3100/dashboard";
const PERF_THRESHOLD = Number(process.env.LIGHTHOUSE_MIN_PERF ?? "0.6");
const ACCESS_THRESHOLD = Number(process.env.LIGHTHOUSE_MIN_A11Y ?? "0.8");
const START_COMMAND = process.env.LIGHTHOUSE_START_COMMAND ?? "npm run dev -- --hostname 127.0.0.1 --port 3100";
const SHOULD_START_SERVER = process.env.LIGHTHOUSE_SKIP_SERVER === "1" ? false : true;
const WAIT_TIMEOUT_MS = Number(process.env.LIGHTHOUSE_WAIT_MS ?? 60_000);

const waitForServer = async (url, timeoutMs) => {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const response = await fetch(url, { method: "GET", redirect: "manual" });
      if (response.ok || (response.status >= 300 && response.status < 400)) {
        return true;
      }
    } catch {
      // Ignore until timeout
    }
    await delay(1500);
  }
  return false;
};

const run = async () => {
  let serverProcess;
  if (SHOULD_START_SERVER) {
    serverProcess = spawn(START_COMMAND, {
      shell: true,
      stdio: "inherit",
      env: {
        ...process.env,
        BROWSER: "none",
      },
    });
  }

  const serverReady = await waitForServer(BASE_URL, WAIT_TIMEOUT_MS);
  if (!serverReady) {
    if (serverProcess) {
      serverProcess.kill("SIGTERM");
    }
    console.error(`Lighthouse: server did not become ready at ${BASE_URL} within ${WAIT_TIMEOUT_MS}ms.`);
    process.exit(1);
  }

  const chrome = await launch({
    chromeFlags: ["--headless", "--no-sandbox", "--disable-gpu"],
  });

  try {
    const runnerResult = await lighthouse(
      BASE_URL,
      {
        port: chrome.port,
        output: "json",
        logLevel: "error",
        onlyCategories: ["performance", "accessibility"],
      },
      undefined
    );

    const performanceScore = runnerResult.lhr.categories.performance?.score ?? 0;
    const accessibilityScore = runnerResult.lhr.categories.accessibility?.score ?? 0;

    console.log(
      `Lighthouse scores → Performance: ${performanceScore.toFixed(2)}, Accessibility: ${accessibilityScore.toFixed(2)}`
    );

    const failures = [];
    if (performanceScore < PERF_THRESHOLD) {
      failures.push(`Performance ${performanceScore.toFixed(2)} < ${PERF_THRESHOLD}`);
    }
    if (accessibilityScore < ACCESS_THRESHOLD) {
      failures.push(`Accessibility ${accessibilityScore.toFixed(2)} < ${ACCESS_THRESHOLD}`);
    }

    if (failures.length) {
      console.error(`Lighthouse thresholds failed: ${failures.join("; ")}`);
      process.exit(1);
    }
  } finally {
    await chrome.kill();
    if (serverProcess) {
      serverProcess.kill("SIGTERM");
    }
  }
};

run().catch((error) => {
  console.error("Lighthouse script failed", error);
  process.exit(1);
});
