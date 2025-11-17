import { rest } from "msw";
import { setupServer } from "msw/node";

import { getIngestJobStatus, startIngestJob } from "@/lib/api/ingestClient";

const apiServer = setupServer();

beforeAll(() => apiServer.listen());
afterEach(() => apiServer.resetHandlers());
afterAll(() => apiServer.close());

const mockJob = {
  task_id: "TASK-UNIT-1",
  state: "PENDING",
  meta: {
    dialect: "returns_report",
  },
};

describe("ingestClient", () => {
  it("posts to the BFF ingest endpoint with query parameters", async () => {
    let capturedSearch: string | null = null;
    apiServer.use(
      rest.post("http://localhost:3000/api/bff/ingest", (req, res, ctx) => {
        capturedSearch = req.url.searchParams.toString();
        return res(ctx.json(mockJob));
      })
    );

    const result = await startIngestJob({ uri: "s3://bucket/report.csv", report_type: "returns", force: true });

    expect(capturedSearch).toContain("uri=s3%3A%2F%2Fbucket%2Freport.csv");
    expect(capturedSearch).toContain("report_type=returns");
    expect(capturedSearch).toContain("force=true");
    expect(result).toEqual(mockJob);
  });

  it("sends multipart form data when a file is provided", async () => {
    const fetchSpy = jest.spyOn(global, "fetch").mockResolvedValue(
      new Response(JSON.stringify(mockJob), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    );

    const file = new File(["a,b\n1,2"], "session.csv", { type: "text/csv" });
    await startIngestJob({ file });

    const [, init] = fetchSpy.mock.calls[0] as [RequestInfo, RequestInit];
    const body = init?.body as FormData;
    expect(body).toBeInstanceOf(FormData);
    expect(body?.get("file")).toBeInstanceOf(File);
    const uploaded = body?.get("file") as File;
    expect(uploaded?.name).toBe("session.csv");

    fetchSpy.mockRestore();
  });

  it("surfaces ApiErrors when the BFF responds with an error", async () => {
    apiServer.use(
      rest.post("http://localhost:3000/api/bff/ingest", (_req, res, ctx) =>
        res(ctx.status(400), ctx.json({ code: "VALIDATION", message: "Bad payload", status: 400 }))
      )
    );

    await expect(startIngestJob({ uri: "s3://invalid" })).rejects.toMatchObject({
      code: "VALIDATION",
      message: "Bad payload",
      status: 400,
    });
  });

  it("fetches job status via the BFF endpoint", async () => {
    apiServer.use(
      rest.get("http://localhost:3000/api/bff/ingest/jobs/TASK-UNIT-JOB", (_req, res, ctx) =>
        res(ctx.json({ task_id: "TASK-UNIT-JOB", state: "SUCCESS", meta: { rows: 12 } }))
      )
    );

    const status = await getIngestJobStatus("TASK-UNIT-JOB");

    expect(status).toMatchObject({ task_id: "TASK-UNIT-JOB", state: "SUCCESS" });
  });
});
