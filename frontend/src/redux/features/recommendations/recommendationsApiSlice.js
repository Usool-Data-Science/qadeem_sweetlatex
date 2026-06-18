import { apiSlice } from "../../services/apiSlice";

export const recommendationsApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // GET /api/recommendations/for-you/?top_k=12
    getForYouRecommendations: builder.query({
      query: (top_k = 12) => ({
        url: "/recommendations/for-you/",
        params: { top_k },
      }),
      providesTags: ["Recommendations"],
    }),

    // GET /api/recommendations/similar/<product_id>/?top_k=12
    getSimilarItems: builder.query({
      query: ({ productId, top_k = 12 }) => ({
        url: `/recommendations/similar/${productId}/`,
        params: { top_k },
      }),
    }),

    // GET /api/recommendations/trending/?top_k=12
    getTrending: builder.query({
      query: (top_k = 12) => ({
        url: "/recommendations/trending/",
        params: { top_k },
      }),
    }),

    // POST /api/recommendations/visual-search/
    visualSearch: builder.mutation({
      query: ({ image_base64, image_url, top_k = 12 }) => ({
        url: "/recommendations/visual-search/",
        method: "POST",
        body: { image_base64, image_url, top_k },
      }),
    }),
  }),
});

export const {
  useGetForYouRecommendationsQuery,
  useGetSimilarItemsQuery,
  useGetTrendingQuery,
  useVisualSearchMutation,
} = recommendationsApiSlice;
