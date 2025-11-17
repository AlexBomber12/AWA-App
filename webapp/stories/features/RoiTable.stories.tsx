import type { Meta, StoryObj } from "@storybook/react";
import { useMemo, useState } from "react";

import { RoiTable } from "@/components/features/roi/RoiTable";
import type { RoiRow } from "@/components/features/roi/types";
import type { RoiSort } from "@/components/features/roi/tableState";

const makeRow = (index: number): RoiRow => ({
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

const meta: Meta<typeof RoiTable> = {
  title: "Features/ROI/RoiTable",
  parameters: {
    layout: "fullscreen",
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
