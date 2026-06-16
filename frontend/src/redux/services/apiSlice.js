import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { Mutex } from "async-mutex";
import { logout, setAuth } from "../features/auth/authSlice";

//  In prodction env, we will leave it blank so it can default to /api which is the backend service endpoint
const BASE_API_URL = import.meta.env.VITE_API_BASE_URL || "";
console.log(BASE_API_URL);

const mutex = new Mutex();
const baseQuery = fetchBaseQuery({
  baseUrl: BASE_API_URL + "/api",
  credentials: "include",
  prepareHeaders: (headers, { getState }) => {
    // Get guestId from auth state
    const guestId = getState().auth.guestId;
    if (guestId) {
      headers.set("X-Session-ID", guestId);
    }
    return headers;
  },
});

const baseQueryWithReauth = async (args, api, extraOptions) => {
  await mutex.waitForUnlock();
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    if (!mutex.isLocked()) {
      const release = await mutex.acquire();
      try {
        const refreshResult = await baseQuery(
          {
            url: "refresh/",
            method: "POST",
          },
          api,
          extraOptions,
        );
        if (refreshResult.data) {
          api.dispatch(setAuth());
          // retry the initial query
          result = await baseQuery(args, api, extraOptions);
        } else {
          // api.dispatch(logout());
        }
      } finally {
        release();
      }
    } else {
      await mutex.waitForUnlock();
      result = await baseQuery(args, api, extraOptions);
    }
  }
  return result;
};

export const apiSlice = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: ["Cart", "User", "Product", "Artist", "Order"],
  endpoints: (builder) => ({}),
});
