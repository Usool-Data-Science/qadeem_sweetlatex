import { apiSlice } from "../../services/apiSlice";

export const productApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/products/ (Supports query params like ?category=... or ?search=...)
    getProducts: builder.query({
      query: (params) => ({
        url: "/products/",
        params: params,
      }),
      providesTags: (result) =>
        result
          ? [
              ...result.products.map(({ product_id: id }) => ({
                type: "Product",
                id,
              })),
              { type: "Product", id: "LIST" },
            ]
          : [{ type: "Product", id: "LIST" }],
    }),

    // GET /api/products/<uuid>/
    getProductDetails: builder.query({
      query: (productId) => `/products/${productId}/`,
      providesTags: (result, error, id) => [{ type: "Product", id }],
    }),

    // POST /api/products/ (For Admin functionality)
    createProduct: builder.mutation({
      query: (data) => ({
        url: "/products/",
        method: "POST",
        body: data,
      }),
      invalidatesTags: [{ type: "Product", id: "LIST" }],
    }),
  }),
});

export const {
  useGetProductsQuery,
  useGetProductDetailsQuery,
  useCreateProductMutation,
} = productApiSlice;
