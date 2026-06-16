import { apiSlice } from "../../services/apiSlice";

export const orderApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/orders/ - To show order history in user profile
    getMyOrders: builder.query({
      query: () => "/orders/",
      providesTags: ["Order"],
    }),

    // GET /api/orders/<id>/ - For the "Thank You" or "Order Summary" page
    getOrderDetails: builder.query({
      query: (id) => `/orders/${id}/`,
      providesTags: (result, error, id) => [{ type: "Order", id }],
    }),

    // POST /api/checkout/ - This returns the Stripe session_url
    createCheckoutSession: builder.mutation({
      query: () => ({
        url: "/checkout/",
        method: "POST",
      }),
      // On success, we invalidate the Cart because the order is now "Pending"
      invalidatesTags: ["Cart"],
    }),
  }),
});

export const {
  useGetMyOrdersQuery,
  useGetOrderDetailsQuery,
  useCreateCheckoutSessionMutation,
} = orderApiSlice;
