import { fetchFromBff } from "@/lib/api/fetchFromBff";
import { useApiQuery } from "@/lib/api/useApiQuery";
import type { paths } from "@/lib/api/types.generated";

import type { ApiError } from "./apiError";

type FastApiSkuResponse = paths["/sku/{asin}"]["get"]["responses"]["200"]["content"]["application/json"];

export type SkuDetail = FastApiSkuResponse & { asin: string };

const SKU_DETAIL_ENDPOINT = "/api/bff/sku";

export async function getSkuDetail(asin: string): Promise<SkuDetail> {
  if (!asin) {
    throw new Error("asin is required to fetch SKU detail");
  }

  const params = new URLSearchParams({ asin });
  const response = await fetchFromBff<FastApiSkuResponse>(`${SKU_DETAIL_ENDPOINT}?${params.toString()}`);
  return {
    ...response,
    asin,
  };
}

const skuDetailQueryKey = (asin: string) => ["sku", "detail", asin] as const;

type UseSkuDetailQueryOptions = {
  enabled?: boolean;
  initialData?: SkuDetail;
};

export function useSkuDetailQuery(asin: string, options?: UseSkuDetailQueryOptions) {
  return useApiQuery<SkuDetail, ApiError, SkuDetail, ReturnType<typeof skuDetailQueryKey>>({
    queryKey: skuDetailQueryKey(asin),
    queryFn: () => getSkuDetail(asin),
    enabled: options?.enabled ?? Boolean(asin),
    initialData: options?.initialData,
  });
}
