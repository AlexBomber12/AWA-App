import { fetchInboxTasks, fetchTaskById, inboxTaskQueryKey, inboxTasksQueryKey } from "@/lib/api/inboxClient";
import { fetchFromBff } from "@/lib/api/fetchFromBff";

jest.mock("@/lib/api/fetchFromBff", () => ({
  fetchFromBff: jest.fn(),
}));

const mockFetch = fetchFromBff as jest.MockedFunction<typeof fetchFromBff>;

describe("inboxClient", () => {
  beforeEach(() => {
    mockFetch.mockReset();
  });

  it("builds query strings for inbox filters", async () => {
    mockFetch.mockResolvedValue({
      items: [],
      pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
    });

    await fetchInboxTasks({
      page: 2,
      pageSize: 10,
      state: "open",
      source: "decision_engine",
      priority: "high",
      assignee: "ops@example.com",
      search: "ROI",
      sort: "deadline",
    });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("page")).toBe("2");
    expect(params.get("pageSize")).toBe("10");
    expect(params.get("state")).toBe("open");
    expect(params.get("source")).toBe("decision_engine");
    expect(params.get("priority")).toBe("high");
    expect(params.get("assignee")).toBe("ops@example.com");
    expect(params.get("search")).toBe("ROI");
    expect(params.get("sort")).toBe("deadline");
    expect(inboxTasksQueryKey({ page: 2, pageSize: 10 })).toEqual(["inbox", "tasks", { page: 2, pageSize: 10 }]);
  });

  it("omits the state filter when set to all", async () => {
    mockFetch.mockResolvedValue({
      items: [],
      pagination: { page: 1, pageSize: 25, total: 0, totalPages: 1 },
    });

    await fetchInboxTasks({ state: "all" });

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    const params = new URL(calledUrl, "http://placeholder").searchParams;
    expect(params.get("state")).toBeNull();
  });

  it("reuses the list endpoint to fetch a single task", async () => {
    mockFetch.mockResolvedValue({
      items: [{ id: "task-123" }],
      pagination: { page: 1, pageSize: 1, total: 1, totalPages: 1 },
    });

    const task = await fetchTaskById("task-123");

    const calledUrl = mockFetch.mock.calls[0]?.[0] as string;
    expect(calledUrl).toContain("taskId=task-123");
    expect(inboxTaskQueryKey("task-123")).toEqual(["inbox", "task", "task-123"]);
    expect(task).toEqual({ id: "task-123" });
  });
});
