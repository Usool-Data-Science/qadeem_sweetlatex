import { useState } from "react";
import Body from "../Components/Body";
import useProduct from "../hooks/use-product";
import { useGetProductsQuery } from "../redux/features/product/productApiSlice";
import GeneralPage from "./GeneralPage";

const LandingPage = () => {
  const PAGE_SIZE = 9;
  const [page, setPage] = useState(1);
  const { data, isLoading, isFetching } = useProduct(page, PAGE_SIZE);
  const handlePageChange = (newPage) => {
    setPage(newPage);
  };

  if (isLoading) {
    return <span className="loading loading-ring loading-lg"></span>;
  }

  return (
    <Body loginButton search>
      <GeneralPage
        data={data}
        page={page}
        onPageChange={handlePageChange}
        isFetching={isFetching}
      />
    </Body>
  );
};

export default LandingPage;
