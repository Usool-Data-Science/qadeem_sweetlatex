import { apiSlice } from "../../services/apiSlice";

export const cartApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/cart/
    getCart: builder.query({
      query: () => "/cart/",
      providesTags: ["Cart"],
    }),

    // POST /api/cart/
    addToCart: builder.mutation({
      query: ({ product_id, size, quantity }) => ({
        url: "/cart/",
        method: "POST",
        body: { product_id, size, quantity },
      }),
      invalidatesTags: ["Cart"],
    }),

    // PATCH /api/cart/item/<id>/
    updateCartItem: builder.mutation({
      query: ({ item_id, action }) => ({
        url: `/cart/item/${item_id}/`,
        method: "PATCH",
        body: { action }, // 'incr' or 'decr'
      }),
      invalidatesTags: ["Cart"],
    }),

    // DELETE /api/cart/item/<id>/
    removeFromCart: builder.mutation({
      query: (item_id) => ({
        url: `/cart/item/${item_id}/`,
        method: "DELETE",
      }),
      invalidatesTags: ["Cart"],
    }),

    // DELETE /api/cart/ (Clear entire cart)
    clearCart: builder.mutation({
      query: () => ({
        url: "/cart/",
        method: "DELETE",
      }),
      invalidatesTags: ["Cart"],
    }),

    // POST /api/checkout/
    checkout: builder.mutation({
      query: () => ({
        url: "/checkout/",
        method: "POST",
      }),
      // We don't necessarily invalidate Cart here because
      // the cart only clears AFTER successful Stripe payment webhook
    }),
  }),
});

export const {
  useGetCartQuery,
  useAddToCartMutation,
  useUpdateCartItemMutation,
  useRemoveFromCartMutation,
  useClearCartMutation,
  useCheckoutMutation,
} = cartApiSlice;
