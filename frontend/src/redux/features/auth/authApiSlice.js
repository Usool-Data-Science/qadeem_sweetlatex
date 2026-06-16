import { apiSlice } from "../../services/apiSlice";
import { setAuth, logout } from "./authSlice";
const authApiSlice = apiSlice.injectEndpoints({
  endpoints: (builder) => ({
    retrieveUser: builder.query({
      query: () => "/users/me/",
      providesTags: ["User"],
    }),

    socialAuthenticate: builder.mutation({
      query: ({ provider, state, code }) => ({
        url: `/o/${provider}.?state=${encodeURIComponent(state)}&code=${encodeURIComponent(code)}/`,
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded",
        },
      }),
    }),

    login: builder.mutation({
      query: ({ email, password }) => ({
        url: "/login/",
        method: "POST",
        body: { email, password },
      }),
      invalidatesTags: ["User", "Cart"],
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;
          dispatch(setAuth(data));
        } catch (err) {}
      },
    }),

    register: builder.mutation({
      query: ({ first_name, last_name, email, password, re_password }) => ({
        url: "/users/",
        method: "POST",
        body: { first_name, last_name, email, password, re_password },
      }),
      invalidatesTags: ["User"],
    }),

    logout: builder.mutation({
      query: () => ({
        url: "/logout/",
        method: "POST",
      }),
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled; // wait for backend to clear cookie
          dispatch(logout()); // then clear Redux state
          dispatch(apiSlice.util.resetApiState());
        } catch (err) {
          // even if backend fails, clear frontend state
          dispatch(logout());
          dispatch(apiSlice.util.resetApiState());
        }
      },
    }),

    resetPassword: builder.mutation({
      query: (email) => ({
        url: "/users/reset_password/",
        method: "POST",
        body: { email },
      }),
    }),

    resetPasswordConfirm: builder.mutation({
      query: ({ uid, token, new_password, re_new_password }) => ({
        url: "/users/reset_password_confirm/",
        method: "POST",
        body: { uid, token, new_password, re_new_password },
      }),
    }),

    contactSupport: builder.mutation({
      query: ({ email, subject, body }) => ({
        url: "/contact-us/",
        method: "POST",
        body: { email, subject, body },
      }),
    }),

    updateUserProfile: builder.mutation({
      query: ({
        first_name,
        last_name,
        email,
        phone_number,
        password,
        old_password,
        street,
        city,
        state,
        country,
        address_type,
        is_default,
      }) => ({
        url: "/users/me/",
        method: "PUT",
        body: {
          first_name,
          last_name,
          email,
          phone_number,
          street,
          city,
          state,
          country,
          address_type,
          is_default,
        },
      }),
      invalidatesTags: ["User"],
    }),

    changeUserPassword: builder.mutation({
      query: ({ new_password, re_new_password, current_password }) => ({
        url: "/users/set_password/",
        method: "POST",
        body: { new_password, re_new_password, current_password },
      }),
      invalidatesTags: ["User"],
    }),
  }),
});

export const {
  useRetrieveUserQuery,
  useSocialAuthenticateMutation,
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useResetPasswordMutation,
  useResetPasswordConfirmMutation,
  useContactSupportMutation,
  useUpdateUserProfileMutation,
  useChangeUserPasswordMutation,
} = authApiSlice;
