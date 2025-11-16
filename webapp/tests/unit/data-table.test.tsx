import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ColumnDef } from "@tanstack/react-table";

import { DataTable } from "@/components/data";

type DemoRow = {
  id: string;
  sku: string;
  status: string;
};

const columns: ColumnDef<DemoRow>[] = [
  {
    header: "SKU",
    accessorKey: "sku",
  },
  {
    header: "Status",
    accessorKey: "status",
  },
];

const rows: DemoRow[] = [
  { id: "1", sku: "SKU-1", status: "pending" },
  { id: "2", sku: "SKU-2", status: "approved" },
];

describe("DataTable", () => {
  it("renders headers and rows", () => {
    render(<DataTable columns={columns} data={rows} />);
    expect(screen.getByText("SKU")).toBeInTheDocument();
    expect(screen.getByText("SKU-1")).toBeInTheDocument();
    expect(screen.getByText("approved")).toBeInTheDocument();
  });

  it("fires onRowClick when a row is clicked", async () => {
    const user = userEvent.setup();
    const handleRowClick = jest.fn();

    render(<DataTable columns={columns} data={rows} onRowClick={handleRowClick} />);

    await user.click(screen.getByText("SKU-2"));
    expect(handleRowClick).toHaveBeenCalledWith(rows[1]);
  });

  it("renders the provided empty state when there is no data", () => {
    render(<DataTable columns={columns} data={[]} emptyState={<p>No rows</p>} />);
    expect(screen.getByText("No rows")).toBeInTheDocument();
  });
});
