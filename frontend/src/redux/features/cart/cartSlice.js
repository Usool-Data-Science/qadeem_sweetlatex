import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  isCartOpen: false,
};

const cartSlice = createSlice({
  name: "cart",
  initialState,
  reducers: {
    toggleCart: (state) => {
      state.isCartOpen = !state.isCartOpen;
    },
    closeCart: (state) => {
      state.isCartOpen = false;
    },
    openCart: (state) => {
      state.isCartOpen = true;
    },
  },
});

export const { toggleCart, closeCart, openCart } = cartSlice.actions;
export default cartSlice.reducer;
