import { useGetProductsQuery } from "../redux/features/product/productApiSlice";

export default function useProduct(params) {
  const { data: products, isLoading } = useGetProductsQuery(params, {
    pollingInterval: 300000,
    refetchOnMountOrArgChange: true,
    refetchOnFocus: true,
    refetchOnReconnect: true,
  });

  return {
    products,
    isLoading,
  };
}
