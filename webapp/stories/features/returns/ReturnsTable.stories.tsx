import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useState } from "react";

import { ErrorState } from "@/components/data";
import { ReturnsTable } from "@/components/features/returns/ReturnsTable";
import type { ApiError } from "@/lib/api/apiError";
import type { ReturnItem, ReturnsSort } from "@/lib/api/returnsClient";

const makeRow = (index: number): ReturnItem => {
  const refund = 25 + index * 3;
  const quantity = (index + 1) * 2;
  return {
    returnId: `RET-${(index + 1).toString().padStart(4, "0")}`,
    asin: `RET-${(index + 1).toString().padStart(4, "0")}`,
    sku: `SKU-${(index + 1).toString().padStart(4, "0")}`,
    quantity,
    reimbursementAmount: refund,
    avgRefundPerUnit: refund / quantity,
    reason: "damaged",
    currency: "EUR",
    status: "paid",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };
};

const ROWS: ReturnItem[] = Array.from({ length: 40 }, (_, index) => makeRow(index));
const MOCK_ERROR: ApiError = { code: "BFF_ERROR", message: "Failed to load returns.", status: 500 };

const meta: Meta<typeof ReturnsTable> = {
  title: "Features/Returns/ReturnsTable",
  parameters: {
    layout: "fullscreen",
  },
};

export default meta;

type Story = StoryObj<typeof ReturnsTable>;

const sortRows = (rows: ReturnItem[], sort: ReturnsSort | undefined) => {
  const next = [...rows];
  switch (sort) {
    case "qty_asc":
      return next.sort((a, b) => a.quantity - b.quantity);
    case "qty_desc":
      return next.sort((a, b) => b.quantity - a.quantity);
    case "refund_asc":
      return next.sort((a, b) => a.reimbursementAmount - b.reimbursementAmount);
    case "asin_asc":
      return next.sort((a, b) => a.asin.localeCompare(b.asin));
    case "asin_desc":
      return next.sort((a, b) => b.asin.localeCompare(a.asin));
    case "refund_desc":
    default:
      return next.sort((a, b) => b.reimbursementAmount - a.reimbursementAmount);
  }
};

const buildPagination = (page: number, pageSize: number, total: number) => ({
  page,
  pageSize,
  total,
  totalPages: Math.max(1, Math.ceil(total / pageSize)),
});

export const Default: Story = {
  render: (args) => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(10);
    const [sort, setSort] = useState<ReturnsSort>("refund_desc");

    const sorted = useMemo(() => sortRows(ROWS, sort), [sort]);
    const rows = useMemo(() => {
      const start = (page - 1) * pageSize;
      return sorted.slice(start, start + pageSize);
    }, [page, pageSize, sorted]);

    const pagination = useMemo(() => buildPagination(page, pageSize, sorted.length), [page, pageSize, sorted.length]);

    return (
      <div className="p-6">
        <ReturnsTable
          {...args}
          rows={rows}
          pagination={pagination}
          page={page}
          pageSize={pageSize}
          sort={sort}
          onPageChange={setPage}
          onPageSizeChange={(nextPageSize) => {
            setPageSize(nextPageSize);
            setPage(1);
          }}
          onSortChange={setSort}
        />
      </div>
    );
  },
};

export const SortedByQuantity: Story = {
  render: (args) => {
    const [sort, setSort] = useState<ReturnsSort>("qty_desc");
    const [pageSize] = useState(8);
    const rows = useMemo(() => sortRows(ROWS, sort).slice(0, pageSize), [sort, pageSize]);
    const pagination = useMemo(() => buildPagination(1, pageSize, ROWS.length), [pageSize]);

    return (
      <div className="p-6">
        <ReturnsTable
          {...args}
          rows={rows}
          pagination={pagination}
          page={1}
          pageSize={pageSize}
          sort={sort}
          onPageChange={() => undefined}
          onPageSizeChange={() => undefined}
          onSortChange={setSort}
        />
      </div>
    );
  },
};

export const LoadingState: Story = {
  args: {
    rows: [],
    pagination: { page: 1, pageSize: 10, total: 0, totalPages: 1 },
    page: 1,
    pageSize: 10,
    sort: "refund_desc",
    onPageChange: () => undefined,
    onPageSizeChange: () => undefined,
    onSortChange: () => undefined,
    isLoading: true,
  },
  render: (args) => (
    <div className="p-6">
      <ReturnsTable {...args} />
    </div>
  ),
};

export const EmptyState: Story = {
  args: {
    rows: [],
    pagination: { page: 1, pageSize: 10, total: 0, totalPages: 1 },
    page: 1,
    pageSize: 10,
    sort: "refund_desc",
    onPageChange: () => undefined,
    onPageSizeChange: () => undefined,
    onSortChange: () => undefined,
  },
  render: (args) => (
    <div className="p-6">
      <ReturnsTable {...args} />
    </div>
  ),
};

export const ErrorExample: Story = {
  render: () => (
    <div className="space-y-4 p-6">
      <ErrorState
        title="Unable to load returns"
        error={MOCK_ERROR}
        onRetry={() => undefined}
      />
      <ReturnsTable
        rows={[]}
        pagination={{ page: 1, pageSize: 10, total: 0, totalPages: 1 }}
        page={1}
        pageSize={10}
        sort="refund_desc"
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
        onSortChange={() => undefined}
      />
    </div>
  ),
};
