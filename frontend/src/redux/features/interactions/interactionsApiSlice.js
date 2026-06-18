import { apiSlice } from "../../services/apiSlice";

export const interactionsApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // POST /api/interactions/log/
    logInteraction: builder.mutation({
      query: ({ product, interaction_type, session_key, metadata }) => ({
        url: "/interactions/log/",
        method: "POST",
        body: { product, interaction_type, session_key, metadata },
      }),
    }),

    // POST /api/interactions/stitch/
    stitchSession: builder.mutation({
      query: (session_key) => ({
        url: "/interactions/stitch/",
        method: "POST",
        body: { session_key },
      }),
    }),
  }),
});

export const { useLogInteractionMutation, useStitchSessionMutation } =
  interactionsApiSlice;
