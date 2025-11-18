import { act, renderHook, waitFor } from "@testing-library/react";

import { useTableState } from "@/lib/tableState";

type Sort = "name_asc" | "name_desc";
type Filters = { search?: string | null };

const DEFAULTS = {
  page: 1,
  pageSize: 25,
  sort: "name_asc" as Sort,
  filters: { search: "" },
};

jest.mock("next/navigation", () => {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  const React = require("react");
  let searchParams = new URLSearchParams();
  const listeners = new Set<() => void>();
  const routerReplace = jest.fn((url: string) => {
    const [, query = ""] = url.split("?");
    searchParams = new URLSearchParams(query);
    listeners.forEach((listener) => listener());
  });

  const subscribe = (listener: () => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  };

  return {
    usePathname: () => "/table-state",
    useRouter: () => ({ replace: routerReplace }),
    useSearchParams: () => {
      const [, forceRender] = React.useState(0);
      React.useEffect(() => {
        const notify = () => forceRender((value: number) => value + 1);
        return subscribe(notify);
      }, []);
      return searchParams;
    },
    __internalNavigationMock: {
      setSearchParams: (query: string) => {
        searchParams = new URLSearchParams(query);
        listeners.forEach((listener) => listener());
      },
      getReplaceCalls: () => routerReplace.mock.calls.map(([url]: [string]) => url),
      reset: () => routerReplace.mockClear(),
    },
  };
});

const getNavigationMock = () =>
  require("next/navigation") as {
    __internalNavigationMock: {
      setSearchParams: (query: string) => void;
      getReplaceCalls: () => string[];
      reset: () => void;
    };
  };

const parseParams = (params: URLSearchParams) => {
  const page = Number(params.get("page"));
  const pageSize = Number(params.get("page_size"));
  const sort = params.get("sort") === "name_desc" ? "name_desc" : ("name_asc" as Sort);
  const search = params.get("filter[search]");
  return {
    page: Number.isFinite(page) ? page : undefined,
    pageSize: Number.isFinite(pageSize) ? pageSize : undefined,
    sort,
    filters: search ? { search } : undefined,
  };
};

const serializeParams = (state: { page: number; pageSize: number; sort?: Sort; filters?: Filters }) => {
  const query = new URLSearchParams();
  query.set("page", String(state.page));
  query.set("page_size", String(state.pageSize));
  if (state.sort) {
    query.set("sort", state.sort);
  }
  if (state.filters?.search) {
    query.set("filter[search]", state.filters.search);
  }
  return query;
};

describe("useTableState", () => {
  beforeEach(() => {
    const navigation = getNavigationMock();
    navigation.__internalNavigationMock.reset();
    navigation.__internalNavigationMock.setSearchParams("");
  });

  it("initialises with defaults when query parameters are missing", () => {
    const { result } = renderHook(() =>
      useTableState<Sort, Filters>({
        defaults: DEFAULTS,
        parseFromSearchParams: parseParams,
        serializeToSearchParams: serializeParams,
      })
    );

    expect(result.current.state).toEqual({
      page: 1,
      pageSize: 25,
      sort: "name_asc",
      filters: { search: "" },
    });
  });

  it("hydrates values from the URL on first render", () => {
    const navigation = getNavigationMock();
    navigation.__internalNavigationMock.setSearchParams("page=3&page_size=50&sort=name_desc&filter%5Bsearch%5D=ops");

    const { result } = renderHook(() =>
      useTableState<Sort, Filters>({
        defaults: DEFAULTS,
        parseFromSearchParams: parseParams,
        serializeToSearchParams: serializeParams,
      })
    );

    expect(result.current.state).toMatchObject({
      page: 3,
      pageSize: 50,
      sort: "name_desc",
      filters: { search: "ops" },
    });
  });

  it("updates the router when state mutators run", () => {
    const navigation = getNavigationMock();
    const { result } = renderHook(() =>
      useTableState<Sort, Filters>({
        defaults: DEFAULTS,
        parseFromSearchParams: parseParams,
        serializeToSearchParams: serializeParams,
      })
    );

    act(() => result.current.setPage(4));
    act(() => result.current.setSort("name_desc"));
    act(() => result.current.setFilters({ search: "widget" }));

    const replaceCalls = navigation.__internalNavigationMock.getReplaceCalls();
    expect(replaceCalls.at(-1)).toContain("page=1");
    expect(replaceCalls.at(-1)).toContain("sort=name_desc");
    expect(replaceCalls.at(-1)).toContain("filter%5Bsearch%5D=widget");
  });

  it("responds to external URL updates", async () => {
    const navigation = getNavigationMock();
    const { result } = renderHook(() =>
      useTableState<Sort, Filters>({
        defaults: DEFAULTS,
        parseFromSearchParams: parseParams,
        serializeToSearchParams: serializeParams,
      })
    );

    act(() => navigation.__internalNavigationMock.setSearchParams("page=2&page_size=10"));

    await waitFor(() => expect(result.current.state.page).toBe(2));
    expect(result.current.state.pageSize).toBe(10);
  });
});
