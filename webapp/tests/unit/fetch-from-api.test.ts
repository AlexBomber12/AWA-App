import { fetchFromApi, isApiError } from "@/lib/api/fetchFromApi";
import { getServerAuthSession } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

const mockGetServerAuthSession = getServerAuthSession as jest.MockedFunction<
  typeof getServerAuthSession
>;

describe("fetchFromApi", () => {
  beforeEach(() => {
    mockGetServerAuthSession.mockResolvedValue({
      user: { roles: ["viewer"] },
      accessToken: "token-123",
      expires: "",
    });
    // @ts-expect-error - override fetch in tests
    global.fetch = jest.fn();
  });

  it("attaches the bearer token and returns JSON", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue({ metric: 42 }),
      headers: new Headers(),
    });

    const data = await fetchFromApi<{ metric: number }>("/stats/kpi");

    expect(data.metric).toBe(42);
    const [, init] = (global.fetch as jest.Mock).mock.calls[0];
    const headers = init.headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer token-123");
  });

  it("throws ApiError when the request fails", async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      status: 500,
      headers: new Headers({ "content-type": "application/json" }),
      json: jest.fn().mockResolvedValue({ detail: "Boom" }),
    });

    await expect(fetchFromApi("/stats/kpi")).rejects.toMatchObject({
      code: "API_ERROR",
      message: "Boom",
      status: 500,
    });
  });

  it("throws UNAUTHORIZED when the session is missing", async () => {
    mockGetServerAuthSession.mockResolvedValueOnce(null);

    try {
      await fetchFromApi("/stats/kpi");
    } catch (error) {
      expect(isApiError(error)).toBe(true);
      if (isApiError(error)) {
        expect(error.code).toBe("UNAUTHORIZED");
      }
    }
  });
});
