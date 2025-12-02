import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useState } from "react";

import { RoiTable } from "@/components/features/roi/RoiTable";
import { ErrorState } from "@/components/data";
import type { RoiItem } from "@/components/features/roi/types";
import type { ApiError } from "@/lib/api/apiError";
import type { RoiSort } from "@/lib/tableState/roi";

const makeRow = (index: number): RoiItem => {
  const cost = 10 + index;
  const freight = 2 + (index % 3);
  const fees = 1.5 + (index % 2);
  const roi = 15 + index;
  const buyPrice = cost + freight + fees;
  const margin = (roi / 100) * buyPrice;
  return {
    sku: `ASIN-${(index + 1).toString().padStart(4, "0")}`,
    asin: `ASIN-${(index + 1).toString().padStart(4, "0")}`,
    title: `Sample ROI SKU ${index + 1}`,
    vendorId: String((index % 5) + 1),
    category: index % 2 === 0 ? "Beauty" : "Outdoors",
    cost,
    freight,
    fees,
    roi,
    margin,
    buyPrice,
    sellPrice: buyPrice + margin,
    currency: "EUR",
  };
};

const MOCK_ROWS: RoiItem[] = Array.from({ length: 50 }, (_, index) => makeRow(index));
const MOCK_ERROR: ApiError = { code: "BFF_ERROR", message: "Backend unavailable", status: 500 };

const meta: Meta<typeof RoiTable> = {
  title: "Features/ROI/RoiTable",
  parameters: {
    layout: "fullscreen",
  },
  argTypes: {
    canApprove: {
      control: { type: "boolean" },
    },
  },
  args: {
    isLoading: false,
    canApprove: true,
  },
};

export default meta;

type Story = StoryObj<typeof RoiTable>;

export const Default: Story = {
  render: (args) => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sort, setSort] = useState<RoiSort>("roi_pct_desc");
    const [selectedAsins, setSelectedAsins] = useState<Set<string>>(new Set());

    const rows = useMemo(() => {
      const start = (page - 1) * pageSize;
      return MOCK_ROWS.slice(start, start + pageSize);
    }, [page, pageSize]);

    const pagination = useMemo(
      () => ({
        page,
        pageSize,
        total: MOCK_ROWS.length,
        totalPages: Math.max(1, Math.ceil(MOCK_ROWS.length / pageSize)),
      }),
      [page, pageSize]
    );

    return (
      <div className="p-6">
        <RoiTable
          {...args}
          rows={rows}
          pagination={pagination}
          page={page}
          pageSize={pageSize}
          sort={sort}
          onPageChange={setPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(1);
          }}
          onSortChange={setSort}
          selectedAsins={selectedAsins}
          onSelectRow={(asin, checked) => {
            setSelectedAsins((current) => {
              const next = new Set(current);
              if (checked) {
                next.add(asin);
              } else {
                next.delete(asin);
              }
              return next;
            });
          }}
          onSelectVisibleRows={(asins, checked) => {
            setSelectedAsins((current) => {
              const next = new Set(current);
              asins.forEach((asin) => {
                if (checked) {
                  next.add(asin);
                } else {
                  next.delete(asin);
                }
              });
              return next;
            });
          }}
        />
      </div>
    );
  },
};
  asin: `ASIN-${(index + 1).toString().padStart(4, "0")}`,
  title: `Sample ROI SKU ${index + 1}`,
  vendor_id: (index % 5) + 1,
  category: index % 2 === 0 ? "Beauty" : "Outdoors",
  cost: 10 + index,
  freight: 2 + (index % 3),
  fees: 1.5 + (index % 2),
  roi_pct: 15 + index,
});

const MOCK_ROWS: RoiRow[] = Array.from({ length: 50 }, (_, index) => makeRow(index));
const MOCK_ERROR: ApiError = { code: "BFF_ERROR", message: "Backend unavailable", status: 500 };

const meta: Meta<typeof RoiTable> = {
  title: "Features/ROI/RoiTable",
  parameters: {
    layout: "fullscreen",
  },
  argTypes: {
    canApprove: {
      control: { type: "boolean" },
    },
  },
  args: {
    isLoading: false,
    canApprove: true,
  },
};

export default meta;

type Story = StoryObj<typeof RoiTable>;

export const Default: Story = {
  render: (args) => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(20);
    const [sort, setSort] = useState<RoiSort>("roi_pct_desc");
    const [selectedAsins, setSelectedAsins] = useState<Set<string>>(new Set());

    const rows = useMemo(() => {
      const start = (page - 1) * pageSize;
      return MOCK_ROWS.slice(start, start + pageSize);
    }, [page, pageSize]);

    const pagination = useMemo(
      () => ({
        page,
        pageSize,
        total: MOCK_ROWS.length,
        totalPages: Math.max(1, Math.ceil(MOCK_ROWS.length / pageSize)),
      }),
      [page, pageSize]
    );

    return (
      <div className="p-6">
        <RoiTable
          {...args}
          rows={rows}
          pagination={pagination}
          page={page}
          pageSize={pageSize}
          sort={sort}
          onPageChange={setPage}
          onPageSizeChange={(size) => {
            setPageSize(size);
            setPage(1);
          }}
          onSortChange={setSort}
          selectedAsins={selectedAsins}
          onSelectRow={(asin, checked) => {
            setSelectedAsins((current) => {
              const next = new Set(current);
              if (checked) {
                next.add(asin);
              } else {
                next.delete(asin);
              }
              return next;
            });
          }}
          onSelectVisibleRows={(asins, checked) => {
            setSelectedAsins((current) => {
              const next = new Set(current);
              asins.forEach((asin) => {
                if (checked) {
                  next.add(asin);
                } else {
                  next.delete(asin);
                }
              });
              return next;
            });
          }}
        />
      </div>
    );
  },
};

export const LoadingState: Story = {
  args: {
    rows: [],
    pagination: { page: 1, pageSize: 20, total: 0, totalPages: 1 },
    page: 1,
    pageSize: 20,
    sort: "roi_pct_desc",
    onSelectRow: () => undefined,
    onSelectVisibleRows: () => undefined,
    onPageChange: () => undefined,
    onPageSizeChange: () => undefined,
    onSortChange: () => undefined,
    isLoading: true,
  },
  render: (args) => (
    <div className="p-6">
      <RoiTable {...args} selectedAsins={new Set()} />
    </div>
  ),
};

export const EmptyState: Story = {
  args: {
    rows: [],
    pagination: { page: 1, pageSize: 20, total: 0, totalPages: 1 },
    page: 1,
    pageSize: 20,
    sort: "roi_pct_desc",
    canApprove: false,
    onSelectRow: () => undefined,
    onSelectVisibleRows: () => undefined,
    onPageChange: () => undefined,
    onPageSizeChange: () => undefined,
    onSortChange: () => undefined,
  },
  render: (args) => (
    <div className="p-6">
      <RoiTable {...args} selectedAsins={new Set()} />
    </div>
  ),
};

export const ReadOnlySelection: Story = {
  render: (args) => {
    const [selected] = useState(new Set<string>(["ASIN-0001", "ASIN-0002"]));
    return (
      <div className="p-6">
        <RoiTable
          {...args}
          canApprove={false}
          selectedAsins={selected}
          rows={MOCK_ROWS.slice(0, 10)}
          pagination={{ page: 1, pageSize: 10, total: 50, totalPages: 5 }}
          page={1}
          pageSize={10}
          sort="asin_asc"
          onPageChange={() => undefined}
          onPageSizeChange={() => undefined}
          onSortChange={() => undefined}
          onSelectRow={() => undefined}
          onSelectVisibleRows={() => undefined}
        />
      </div>
    );
  },
};

export const SortedByVendor: Story = {
  render: (args) => {
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(15);
    const [sort, setSort] = useState<RoiSort>("vendor_desc");
    const sortedRows = useMemo(
      () => [...MOCK_ROWS].sort((a, b) => Number(b.vendorId ?? 0) - Number(a.vendorId ?? 0)),
      []
    );
    const rows = useMemo(() => {
      const start = (page - 1) * pageSize;
      return sortedRows.slice(start, start + pageSize);
    }, [page, pageSize, sortedRows]);

    const pagination = useMemo(
      () => ({
        page,
        pageSize,
        total: sortedRows.length,
        totalPages: Math.max(1, Math.ceil(sortedRows.length / pageSize)),
      }),
      [page, pageSize, sortedRows.length]
    );

    return (
      <div className="p-6">
        <RoiTable
          {...args}
          canApprove={false}
          rows={rows}
          pagination={pagination}
          page={page}
          pageSize={pageSize}
          sort={sort}
          onPageChange={setPage}
          onPageSizeChange={(next) => {
            setPageSize(next);
            setPage(1);
          }}
          onSortChange={setSort}
          selectedAsins={new Set()}
          onSelectRow={() => undefined}
          onSelectVisibleRows={() => undefined}
        />
      </div>
    );
  },
};

export const ErrorExample: Story = {
  render: () => (
    <div className="space-y-4 p-6">
      <ErrorState
        title="Unable to load ROI rows"
        error={MOCK_ERROR}
        onRetry={() => undefined}
      />
      <RoiTable
        rows={[]}
        pagination={{ page: 1, pageSize: 50, total: 0, totalPages: 1 }}
        page={1}
        pageSize={50}
        sort="roi_pct_desc"
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
        onSortChange={() => undefined}
        selectedAsins={new Set()}
        onSelectRow={() => undefined}
        onSelectVisibleRows={() => undefined}
        canApprove={false}
      />
    </div>
  ),
};
