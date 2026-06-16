import Archive from "../Components/Archive";
import Body from "../Components/Body";
import useProduct from "../hooks/use-product";

import { useGetProductsQuery } from "../redux/features/product/productApiSlice";

const ArchivePage = () => {
  // const { data: products, isLoading } = useGetProductsQuery();
  const { products, isLoading } = useProduct();
  const archiveProducts = products?.products.filter(
    (prod) => prod.is_expired === true || prod.is_sold_out === true,
  );

  return (
    <Body>
      <div className="py-6 grow-1 font-courier">
        {isLoading && <span className="loading loading-ring loading-lg"></span>}

        {archiveProducts?.length === 0 && (
          <span className="grid place-content-center"> Archive is empty!</span>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
          {archiveProducts?.length > 0 &&
            archiveProducts.map((product, index) => (
              <Archive
                key={index}
                id={product.product_id}
                title={product.title}
                artist={product.artist_name}
                image={product.images[0]}
              />
            ))}
        </div>
      </div>
    </Body>
  );
};

export default ArchivePage;
