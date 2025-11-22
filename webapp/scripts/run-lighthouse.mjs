#!/usr/bin/env node

import { spawn } from "node:child_process";
import net from "node:net";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import os from "node:os";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

import lighthouse from "lighthouse";
import { launch } from "chrome-launcher";

const PERF_THRESHOLD = Number(process.env.LIGHTHOUSE_MIN_PERF ?? "0.6");
const ACCESS_THRESHOLD = Number(process.env.LIGHTHOUSE_MIN_A11Y ?? "0.8");
const SHOULD_START_SERVER = process.env.LIGHTHOUSE_SKIP_SERVER === "1" ? false : true;
const WAIT_TIMEOUT_MS = Number(process.env.LIGHTHOUSE_WAIT_MS ?? 60_000);
const DEFAULT_PORT = Number(process.env.LIGHTHOUSE_PORT ?? "3100");
const DEFAULT_BASE = process.env.LIGHTHOUSE_URL;
const PORT_SCAN_ATTEMPTS = Number(process.env.LIGHTHOUSE_PORT_ATTEMPTS ?? "20");
const LIGHTHOUSE_MODE = process.env.LIGHTHOUSE_MODE ?? "prod"; // prod | dev
const BUILD_COMMAND = process.env.LIGHTHOUSE_BUILD_COMMAND ?? "npm run build";

const findAvailablePort = async (startPort) => {
  let port = startPort;
  for (let attempt = 0; attempt < PORT_SCAN_ATTEMPTS; attempt += 1) {
    try {
      await new Promise((resolve, reject) => {
        const server = net.createServer();
        server.once("error", reject);
        server.listen(port, "127.0.0.1", () => {
          server.close(() => resolve(port));
        });
      });
      return port;
    } catch (error) {
      if (error?.code === "EADDRINUSE") {
        port += 1;
        continue;
      }
      throw error;
    }
  }
  throw new Error("Unable to find available port for Lighthouse dev server");
};

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

const resolveChromePath = async () => {
  try {
    const { chromium } = await import("playwright");
    const executable = chromium.executablePath();
    if (existsSync(executable)) {
      return executable;
    }

    console.warn("Playwright Chromium not found. Installing Chromium for Lighthouse...");
    await new Promise((resolve, reject) => {
      const install = spawn("npx", ["playwright", "install", "chromium"], {
        shell: true,
        stdio: "inherit",
      });
      install.on("exit", (code) => {
        if (code === 0) {
          resolve(null);
        } else {
          reject(new Error(`playwright install exited with code ${code}`));
        }
      });
    });
    const refreshed = chromium.executablePath();
    if (existsSync(refreshed)) {
      return refreshed;
    }
  } catch (error) {
    console.warn("Unable to resolve Playwright Chromium, falling back to system Chrome.", error?.message);
  }

  return undefined;
};

const run = async () => {
  let baseUrl = DEFAULT_BASE;
  let resolvedPort = DEFAULT_PORT;

  if (baseUrl) {
    const parsed = new URL(baseUrl);
    resolvedPort = Number(parsed.port || DEFAULT_PORT);
  } else {
    resolvedPort = SHOULD_START_SERVER ? await findAvailablePort(DEFAULT_PORT) : DEFAULT_PORT;
    baseUrl = `http://127.0.0.1:${resolvedPort}/dashboard`;
  }

  const startCommand =
    process.env.LIGHTHOUSE_START_COMMAND ??
    (LIGHTHOUSE_MODE === "prod"
      ? `npm run start -- --hostname 127.0.0.1 --port ${resolvedPort}`
      : `npm run dev -- --hostname 127.0.0.1 --port ${resolvedPort}`);

  let serverProcess;
  if (SHOULD_START_SERVER) {
    if (LIGHTHOUSE_MODE === "prod") {
      console.log(`Lighthouse: building app with "${BUILD_COMMAND}"...`);
      await new Promise((resolve, reject) => {
        const build = spawn(BUILD_COMMAND, { shell: true, stdio: "inherit", env: process.env });
        build.on("exit", (code) => {
          if (code === 0) {
            resolve(null);
          } else {
            reject(new Error(`Build failed with exit code ${code}`));
          }
        });
      });
    }

    serverProcess = spawn(startCommand, {
      shell: true,
      stdio: "inherit",
      env: {
        ...process.env,
        BROWSER: "none",
      },
    });
  }

  const serverReady = await waitForServer(baseUrl, WAIT_TIMEOUT_MS);
  if (!serverReady) {
    if (serverProcess) {
      serverProcess.kill("SIGTERM");
    }
    console.error(`Lighthouse: server did not become ready at ${baseUrl} within ${WAIT_TIMEOUT_MS}ms.`);
    process.exit(1);
  }

  const tmpRoot = process.env.LIGHTHOUSE_TMP ?? (path.isAbsolute(os.tmpdir()) ? os.tmpdir() : "/tmp");
  const userDataDir = mkdtempSync(path.join(tmpRoot, "lighthouse-user-"));

  const chrome = await launch({
    chromeFlags: ["--headless", "--no-sandbox", "--disable-gpu"],
    chromePath: await resolveChromePath(),
    userDataDir,
  });

  try {
    const runnerResult = await lighthouse(
      baseUrl,
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
    rmSync(userDataDir, { recursive: true, force: true });
    if (serverProcess) {
      serverProcess.kill("SIGTERM");
    }
  }
};

run().catch((error) => {
  console.error("Lighthouse script failed", error);
  process.exit(1);
});
