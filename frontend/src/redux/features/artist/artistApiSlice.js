import { apiSlice } from "../../services/apiSlice";

export const artistApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    // Fetches all artists (used for the dropdowns in NewProduct)
    getArtists: builder.query({
      query: () => ({
        url: "/artists/",
        method: "GET",
      }),
      // Provides tags so if we add an artist, the list refreshes automatically
      providesTags: ["Artist"],
    }),

    // Create a new artist profile
    createArtist: builder.mutation({
      query: (newArtist) => ({
        url: "/artists/",
        method: "POST",
        body: newArtist,
      }),
      invalidatesTags: ["Artist"],
    }),

    // Get a single artist's details
    getArtistDetails: builder.query({
      query: (id) => ({
        url: `/artists/${id}/`,
        method: "GET",
      }),
      providesTags: (result, error, id) => [{ type: "Artist", id }],
    }),
  }),
});

export const {
  useGetArtistsQuery,
  useCreateArtistMutation,
  useGetArtistDetailsQuery,
} = artistApiSlice;
