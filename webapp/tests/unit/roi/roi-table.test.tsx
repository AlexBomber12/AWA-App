import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RoiTable } from "@/components/features/roi/RoiTable";

jest.mock("@/components/data", () => {
  const Actual = jest.requireActual("@/components/data");
  return {
    ...Actual,
    VirtualizedTable: ({
      columns,
      data,
      getRowId,
      getRowClassName,
      isLoading,
    }: {
      columns: any[];
      data: any[];
      getRowId?: (row: any, index: number) => string;
      getRowClassName?: (row: any) => string | undefined;
      isLoading?: boolean;
    }) => (
      <div>
        <div role="rowgroup">
          {columns.map((column) => (
            <div key={column.id ?? column.accessorKey}>
              {typeof column.header === "function" ? column.header() : column.header}
            </div>
          ))}
        </div>
        {isLoading ? <div>Loading rows…</div> : null}
        <div>
          {data.map((row, index) => (
            <div
              key={getRowId ? getRowId(row, index) : index}
              className={getRowClassName ? getRowClassName({ original: row } as any) : undefined}
            >
              {columns.map((column) => (
                <span key={column.id ?? column.accessorKey}>
                  {column.cell ? column.cell({ row: { original: row } } as any) : null}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
    ),
    PaginationControls: ({
      page,
      pageSize,
      totalItems,
      onPageChange,
      onPageSizeChange,
    }: {
      page: number;
      pageSize: number;
      totalItems: number;
      onPageChange: (page: number) => void;
      onPageSizeChange: (pageSize: number) => void;
    }) => (
      <div>
        <button onClick={() => onPageChange(page + 1)}>Next</button>
        <button onClick={() => onPageSizeChange(pageSize * 2)}>PageSize</button>
        <span data-testid="total-items">{totalItems}</span>
      </div>
    ),
  };
});

const pushSpy = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushSpy }),
}));

describe("RoiTable", () => {
  const user = userEvent.setup();
  beforeEach(() => {
    pushSpy.mockReset();
  });

  const rows = [
    {
      asin: "B00-ROI-1",
      title: "First ROI SKU",
      vendor_id: 10,
      category: "Beauty",
      cost: 10,
      freight: 2,
      fees: 1,
      roi_pct: 20,
    },
    {
      asin: "B00-ROI-2",
      title: "Second ROI SKU",
      vendor_id: 11,
      category: "Outdoors",
      cost: 12,
      freight: 3,
      fees: 1.5,
      roi_pct: 15,
    },
  ];

  it("renders ROI rows and wires selection, sorting, and pagination handlers", async () => {
    const onPageChange = jest.fn();
    const onPageSizeChange = jest.fn();
    const onSortChange = jest.fn();
    const onSelectRow = jest.fn();
    const onSelectVisibleRows = jest.fn();

    render(
      <RoiTable
        rows={rows}
        pagination={{ page: 1, pageSize: 50, total: 2, totalPages: 1 }}
        page={1}
        pageSize={50}
        onPageChange={onPageChange}
        onPageSizeChange={onPageSizeChange}
        sort="asin_asc"
        onSortChange={onSortChange}
        selectedAsins={new Set(["B00-ROI-1"])}
        onSelectRow={onSelectRow}
        onSelectVisibleRows={onSelectVisibleRows}
        canApprove
      />
    );

    expect((screen.getByLabelText("Select B00-ROI-1") as HTMLInputElement).checked).toBe(true);
    expect(screen.getByTestId("total-items")).toHaveTextContent("2");

    await user.click(screen.getByRole("button", { name: /SKU/ }));
    expect(onSortChange).toHaveBeenCalledWith("asin_desc");

    await user.click(screen.getByLabelText("Select visible rows"));
    expect(onSelectVisibleRows).toHaveBeenCalledWith(["B00-ROI-1", "B00-ROI-2"], true);

    await user.click(screen.getByLabelText("Select B00-ROI-2"));
    expect(onSelectRow).toHaveBeenCalledWith("B00-ROI-2", true);

    await user.click(screen.getAllByRole("button", { name: "B00-ROI-1" })[0]);
    expect(pushSpy).toHaveBeenCalledWith("/sku/B00-ROI-1");

    await user.click(screen.getByRole("button", { name: "Next" }));
    expect(onPageChange).toHaveBeenCalledWith(2);

    await user.click(screen.getByRole("button", { name: "PageSize" }));
    expect(onPageSizeChange).toHaveBeenCalledWith(100);
  });

  it("shows a loading state when rows are pending", () => {
    render(
      <RoiTable
        rows={rows}
        pagination={{ page: 1, pageSize: 50, total: 2, totalPages: 1 }}
        page={1}
        pageSize={50}
        onPageChange={() => {}}
        onPageSizeChange={() => {}}
        onSortChange={() => {}}
        onSelectRow={() => {}}
        onSelectVisibleRows={() => {}}
        selectedAsins={new Set()}
        canApprove={false}
        isLoading
      />
    );

    expect(screen.getByText(/Loading rows/)).toBeInTheDocument();
  });
});
