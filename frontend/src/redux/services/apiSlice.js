import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import { Mutex } from "async-mutex";
import { logout, setAuth } from "../features/auth/authSlice";

const BASE_API_URL = import.meta.env.VITE_API_BASE_URL || "";

const mutex = new Mutex();

const baseQuery = fetchBaseQuery({
  baseUrl: BASE_API_URL + "/api",
  credentials: "include",
  prepareHeaders: (headers, { getState }) => {
    const guestId = getState().auth.guestId;
    if (guestId) {
      headers.set("X-Session-ID", guestId);
    }
    return headers;
  },
});

const baseQueryWithReauth = async (args, api, extraOptions) => {
  // ── Guard: never attempt refresh when user is already logged out ──────────
  // This is the primary fix. If Redux state says the user is not
  // authenticated, we skip the 401 → refresh → retry cycle entirely.
  // The request still runs (some endpoints are public), but on 401 we
  // dispatch logout and return the error cleanly without any retry loop.
  const isAuthenticated = api.getState().auth.isAuthenticated;

  await mutex.waitForUnlock();
  let result = await baseQuery(args, api, extraOptions);

  if (result.error && result.error.status === 401) {
    // If the user was already logged out, just dispatch logout to ensure
    // Redux state is clean and return the error. No refresh attempt.
    if (!isAuthenticated) {
      api.dispatch(logout());
      return result;
    }

    // User was authenticated — access token has expired. Attempt one refresh.
    if (!mutex.isLocked()) {
      const release = await mutex.acquire();
      try {
        const refreshResult = await baseQuery(
          { url: "refresh/", method: "POST" },
          api,
          extraOptions,
        );

        if (refreshResult.data) {
          // Refresh succeeded — update auth state and retry original request
          api.dispatch(setAuth());
          result = await baseQuery(args, api, extraOptions);
        } else {
          // Refresh failed — session is truly expired. Log out cleanly.
          // This dispatches logout() which clears localStorage and Redux state,
          // preventing any further 401 → refresh loops.
          api.dispatch(logout());
          api.dispatch(apiSlice.util.resetApiState());
        }
      } finally {
        release();
      }
    } else {
      // Another request is already refreshing — wait for it, then retry.
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
