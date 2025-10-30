import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.K6_BASE_URL || __ENV.API_BASE || "http://localhost:8000";

export const options = {
  thresholds: {
    "http_req_duration{expected_response:true}": ["p(95)<300"],
  },
};

export default function () {
  const endpoints = ["/ready", "/health", "/metrics"];
  for (const path of endpoints) {
    const response = http.get(`${BASE}${path}`);
    check(response, {
      [`${path} responded 200`]: (r) => r.status === 200,
    });
  }
  sleep(5);
}
