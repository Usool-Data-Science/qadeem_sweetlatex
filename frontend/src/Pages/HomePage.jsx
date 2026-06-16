import Body from "../Components/Body";
import useProduct from "../hooks/use-product";
import { useGetProductsQuery } from "../redux/features/product/productApiSlice";
import GeneralPage from "./GeneralPage";

const HomePage = () => {
  // const { data: products, isLoading } = useGetProductsQuery();
  const { products, isLoading } = useProduct();

  if (isLoading) {
    return <span className="loading loading-ring loading-lg"></span>;
  }

  return (
    <Body search>
      <GeneralPage products={products?.products} />
    </Body>
  );
};

export default HomePage;
