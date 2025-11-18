import type { Meta, StoryObj } from "@storybook/react";

import { SkuPage } from "@/components/features/sku/SkuPage";
import type { SkuDetail } from "@/lib/api/skuClient";

import { FetchMock, type FetchMockHandler } from "../../utils/fetchMock";

const mockDetail: SkuDetail = {
  asin: "B00-STORY-001",
  title: "Storybook Prime Hydration Pack",
  roi: 42.3,
  fees: 11.2,
  chartData: [
    { date: "2025-02-07T00:00:00Z", price: 32.5 },
    { date: "2025-02-08T00:00:00Z", price: 34.1 },
    { date: "2025-02-09T00:00:00Z", price: 33.4 },
    { date: "2025-02-10T00:00:00Z", price: 35.8 },
    { date: "2025-02-11T00:00:00Z", price: 36.4 },
    { date: "2025-02-12T00:00:00Z", price: 38.2 },
  ],
};

const meta: Meta<typeof SkuPage> = {
  title: "Features/SKU/SkuPage",
  component: SkuPage,
  args: {
    asin: mockDetail.asin,
    from: "roi",
    initialData: mockDetail,
    fetchEnabled: false,
  },
};

export default meta;

type Story = StoryObj<typeof SkuPage>;

export const Default: Story = {};

export const SparseHistory: Story = {
  args: {
    from: "returns",
    initialData: {
      ...mockDetail,
      asin: "B00-STORY-EDGE",
      title: "Storybook Edge Case SKU",
      chartData: [{ date: "2025-02-12T00:00:00Z", price: 28.5 }],
      roi: 18.2,
      fees: 15.4,
    },
  },
};

export const Loading: Story = {
  args: {
    initialData: undefined,
    fetchEnabled: false,
  },
};

export const MissingAsin: Story = {
  args: {
    asin: "",
    fetchEnabled: false,
  },
};

export const ErrorState: Story = {
  args: {
    initialData: undefined,
    fetchEnabled: true,
  },
  render: (args) => {
    const handlers: FetchMockHandler[] = [
      {
        predicate: ({ url }) => url.includes("/api/bff/sku"),
        response: () =>
          new Response(
            JSON.stringify({
              code: "BFF_ERROR",
              message: "Simulated failure fetching SKU detail.",
            }),
            {
              status: 500,
              headers: { "Content-Type": "application/json" },
            }
          ),
      },
    ];

    return (
      <FetchMock handlers={handlers}>
        <SkuPage {...args} />
      </FetchMock>
    );
  },
};
