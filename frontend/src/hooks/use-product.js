import { useGetProductsQuery } from "../redux/features/product/productApiSlice";

/**
 * useProduct(page, pageSize)
 *
 * Wraps RTK Query's getProducts with sensible cache behaviour:
 *   - refetchOnMountOrArgChange: true — re-fetches when page changes
 *   - refetchOnFocus: false — do NOT re-fetch every time the tab regains focus.
 *     This was the main cause of the "cache keeps clearing" experience.
 *     The Django backend + RTK Query cache (keepUnusedDataFor: 300s) handles
 *     freshness; we don't need aggressive polling on top.
 *   - pollingInterval: 0 — disabled. Products change infrequently; cache
 *     invalidation via invalidatesTags handles updates.
 */
export default function useProduct(page = 1, pageSize = 9) {
  const { data, isLoading, isFetching } = useGetProductsQuery(
    { page, page_size: pageSize },
    {
      refetchOnMountOrArgChange: true,
      refetchOnFocus: false,
      refetchOnReconnect: true,
      pollingInterval: 0,
    },
  );

  return {
    data, // full response: { products, total, page, total_pages, ... }
    isLoading,
    isFetching, // true when fetching a new page (not first load)
  };
}
