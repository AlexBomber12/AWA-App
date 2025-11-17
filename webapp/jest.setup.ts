import "@testing-library/jest-dom";
import { ReadableStream, TransformStream, WritableStream } from "stream/web";
import { TextDecoder, TextEncoder } from "util";
import { BroadcastChannel } from "worker_threads";

process.env.NEXT_PUBLIC_API_URL ??= "http://localhost:8000";
process.env.NEXT_PUBLIC_WEBAPP_URL ??= "http://localhost:3000";
process.env.NEXT_PUBLIC_APP_ENV ??= "test";
process.env.KEYCLOAK_ISSUER ??= "http://localhost:8080/realms/awa";
process.env.KEYCLOAK_CLIENT_ID ??= "awa-webapp";
process.env.KEYCLOAK_CLIENT_SECRET ??= "jest-secret";
process.env.NEXTAUTH_URL ??= "http://localhost:3000";
process.env.NEXTAUTH_SECRET ??= "jest-nextauth-secret";

type GlobalWithPolyfills = typeof globalThis & {
  TextEncoder?: typeof TextEncoder;
  TextDecoder?: typeof TextDecoder;
  ReadableStream?: typeof ReadableStream;
  WritableStream?: typeof WritableStream;
  TransformStream?: typeof TransformStream;
  BroadcastChannel?: typeof BroadcastChannel;
  fetch?: typeof fetch;
  Headers?: typeof Headers;
  Request?: typeof Request;
  Response?: typeof Response;
  ResizeObserver?: typeof ResizeObserver;
};

const globalThisWithPolyfills = globalThis as GlobalWithPolyfills;

if (!globalThisWithPolyfills.TextEncoder) {
  globalThisWithPolyfills.TextEncoder = TextEncoder as GlobalWithPolyfills["TextEncoder"];
}

if (!globalThisWithPolyfills.TextDecoder) {
  globalThisWithPolyfills.TextDecoder = TextDecoder as GlobalWithPolyfills["TextDecoder"];
}

if (!globalThisWithPolyfills.ReadableStream) {
  globalThisWithPolyfills.ReadableStream = ReadableStream as GlobalWithPolyfills["ReadableStream"];
}

if (!globalThisWithPolyfills.WritableStream) {
  globalThisWithPolyfills.WritableStream = WritableStream as GlobalWithPolyfills["WritableStream"];
}

if (!globalThisWithPolyfills.TransformStream) {
  globalThisWithPolyfills.TransformStream = TransformStream as GlobalWithPolyfills["TransformStream"];
}

if (!globalThisWithPolyfills.BroadcastChannel) {
  globalThisWithPolyfills.BroadcastChannel = BroadcastChannel as GlobalWithPolyfills["BroadcastChannel"];
}

const loadUndici = () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require("undici");
};

if (!globalThisWithPolyfills.fetch) {
  const { fetch } = loadUndici();
  globalThisWithPolyfills.fetch = fetch as GlobalWithPolyfills["fetch"];
}

if (!globalThisWithPolyfills.Headers) {
  const { Headers } = loadUndici();
  globalThisWithPolyfills.Headers = Headers as GlobalWithPolyfills["Headers"];
}

if (!globalThisWithPolyfills.Request) {
  const { Request } = loadUndici();
  globalThisWithPolyfills.Request = Request as GlobalWithPolyfills["Request"];
}

if (!globalThisWithPolyfills.Response) {
  const { Response } = loadUndici();
  globalThisWithPolyfills.Response = Response as GlobalWithPolyfills["Response"];
}

if (!("ResizeObserver" in globalThisWithPolyfills)) {
  class MockResizeObserver {
    observe() {
      return undefined;
    }
    unobserve() {
      return undefined;
    }
    disconnect() {
      return undefined;
    }
  }
  globalThisWithPolyfills.ResizeObserver = MockResizeObserver as typeof ResizeObserver;
}
