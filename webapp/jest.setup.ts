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

if (typeof global.TextEncoder === "undefined") {
  // @ts-expect-error - jsdom types don't include util encoders
  global.TextEncoder = TextEncoder;
}

if (typeof global.TextDecoder === "undefined") {
  // @ts-expect-error - jsdom types don't include util encoders
  global.TextDecoder = TextDecoder;
}

if (typeof global.ReadableStream === "undefined") {
  // @ts-expect-error - jsdom types don't include stream/web globals
  global.ReadableStream = ReadableStream;
}

if (typeof global.WritableStream === "undefined") {
  // @ts-expect-error - jsdom types don't include stream/web globals
  global.WritableStream = WritableStream;
}

if (typeof global.TransformStream === "undefined") {
  // @ts-expect-error - jsdom types don't include stream/web globals
  global.TransformStream = TransformStream;
}

if (typeof global.BroadcastChannel === "undefined") {
  // @ts-expect-error - BroadcastChannel types are provided by worker_threads here
  global.BroadcastChannel = BroadcastChannel;
}

const loadUndici = () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  return require("undici");
};

if (typeof global.fetch === "undefined") {
  const { fetch } = loadUndici();
  // @ts-expect-error - undici types align with the Fetch API
  global.fetch = fetch;
}

if (typeof global.Headers === "undefined") {
  const { Headers } = loadUndici();
  // @ts-expect-error - undici types align with the Fetch API
  global.Headers = Headers;
}

if (typeof global.Request === "undefined") {
  const { Request } = loadUndici();
  // @ts-expect-error - undici types align with the Fetch API
  global.Request = Request;
}

if (typeof global.Response === "undefined") {
  const { Response } = loadUndici();
  // @ts-expect-error - undici types align with the Fetch API
  global.Response = Response;
}
