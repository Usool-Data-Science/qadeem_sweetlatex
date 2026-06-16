import { createSlice } from "@reduxjs/toolkit";
import { v4 as uuidv4 } from "uuid";

const userFromStorage = localStorage.getItem("userInfo")
  ? JSON.parse(localStorage.getItem("userInfo"))
  : null;

// Function to initialize guestId - called only once when store is created
const initializeGuestId = () => {
  const stored = localStorage.getItem("guestId");
  if (stored) {
    return stored;
  }
  const newGuestId = uuidv4();
  localStorage.setItem("guestId", newGuestId);
  return newGuestId;
};

const initialState = {
  user: userFromStorage,
  guestId: initializeGuestId(),
  isAuthenticated: !!userFromStorage,
  loading: false,
  error: null,
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setAuth: (state, action) => {
      state.isAuthenticated = true;
      if (action.payload) {
        state.user = action.payload;
        localStorage.setItem("userInfo", JSON.stringify(action.payload));
      }
    },
    logout: (state) => {
      state.user = null;
      state.guestId = uuidv4();
      state.isAuthenticated = false;
      localStorage.setItem("guestId", state.guestId);
      localStorage.removeItem("userInfo");
    },
    finishInitialLoad: (state) => {
      state.loading = false;
    },
    generateNewGuestId: (state) => {
      state.guestId = uuidv4();
      localStorage.setItem("guestId", state.guestId);
    },
  },
});

export const { setAuth, logout, finishInitialLoad } = authSlice.actions;
export default authSlice.reducer;
