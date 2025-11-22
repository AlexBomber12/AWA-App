import { fetchFromBff } from "@/lib/api/fetchFromBff";

const originalEnv = { ...process.env };

describe("fetchFromBff", () => {
  beforeEach(() => {
    jest.restoreAllMocks();
    process.env = { ...originalEnv };
  });

  it("builds a URL from NEXT_PUBLIC_WEBAPP_URL for relative paths", async () => {
    process.env.NEXT_PUBLIC_WEBAPP_URL = "https://preview.awaconsole.test";
    const fetchSpy = jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await fetchFromBff("/api/bff/roi");

    expect(fetchSpy).toHaveBeenCalledWith(
      "https://preview.awaconsole.test/api/bff/roi",
      expect.objectContaining({ credentials: "same-origin" })
    );
  });

  it("passes through absolute URLs untouched", async () => {
    const fetchSpy = jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    await fetchFromBff("https://api.example.com/health");

    expect(fetchSpy).toHaveBeenCalledWith(
      "https://api.example.com/health",
      expect.objectContaining({ credentials: "same-origin" })
    );
  });

  it("returns undefined for 204 responses", async () => {
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(null, {
        status: 204,
      })
    );

    const result = await fetchFromBff("/api/bff/noop");

    expect(result).toBeUndefined();
  });

  it("surfaces ApiError details when the BFF returns JSON error payloads", async () => {
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ code: "BFF_ERROR", message: "Boom" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      })
    );

    await expect(fetchFromBff("/api/bff/stats")).rejects.toMatchObject({
      code: "BFF_ERROR",
      message: "Boom",
      status: 502,
    });
  });

  it("wraps non-JSON error payloads into ApiError", async () => {
    jest.spyOn(console, "error").mockImplementation(() => {});
    jest.spyOn(global, "fetch").mockResolvedValue(
      new Response("Gateway timeout", {
        status: 504,
        headers: { "Content-Type": "text/plain" },
      })
    );

    await expect(fetchFromBff("/api/bff/stats")).rejects.toMatchObject({
      code: "BFF_ERROR",
      message: expect.stringContaining("504"),
      status: 504,
    });
  });
});
