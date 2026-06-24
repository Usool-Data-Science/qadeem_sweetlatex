import { apiSlice } from "../../services/apiSlice";

export const productApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/products/?page=1&page_size=9
    // Cache key includes page + page_size so each page is stored independently.
    // keepUnusedDataFor: 300 — keep cached pages for 5 minutes after the
    // component unmounts (so navigating back doesn't re-fetch).
    getProducts: builder.query({
      query: ({ page = 1, page_size = 9 } = {}) => ({
        url: "/products/",
        params: { page, page_size },
      }),
      keepUnusedDataFor: 300,
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
      keepUnusedDataFor: 300,
      providesTags: (result, error, id) => [{ type: "Product", id }],
    }),

    // POST /api/products/
    createProduct: builder.mutation({
      query: (data) => ({
        url: "/products/",
        method: "POST",
        body: data,
      }),
      // Invalidate ALL cached product list pages
      invalidatesTags: [{ type: "Product", id: "LIST" }],
    }),

    // PATCH /api/products/<uuid>/
    updateProduct: builder.mutation({
      query: ({ id, data }) => ({
        url: `/products/${id}/`,
        method: "PATCH",
        body: data,
      }),
      invalidatesTags: (result, error, { id }) => [
        { type: "Product", id },
        { type: "Product", id: "LIST" },
      ],
    }),

    // DELETE /api/products/<uuid>/
    deleteProduct: builder.mutation({
      query: (id) => ({
        url: `/products/${id}/`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, id) => [
        { type: "Product", id },
        { type: "Product", id: "LIST" },
      ],
    }),
  }),
});

export const {
  useGetProductsQuery,
  useGetProductDetailsQuery,
  useCreateProductMutation,
  useUpdateProductMutation,
  useDeleteProductMutation,
} = productApiSlice;
