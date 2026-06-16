import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  currentStep: 1, // 1: Cart, 2: Shipping, 3: Payment
  lastOrderId: null,
  isProcessing: false,
};

const orderSlice = createSlice({
  name: "orders",
  initialState,
  reducers: {
    setCheckoutStep: (state, action) => {
      state.currentStep = action.payload;
    },
    setProcessing: (state, action) => {
      state.isProcessing = action.payload;
    },
    setLastOrder: (state, action) => {
      state.lastOrderId = action.payload;
    },
    resetCheckout: (state) => {
      state.currentStep = 1;
      state.isProcessing = false;
    },
  },
});

export const { setCheckoutStep, setProcessing, setLastOrder, resetCheckout } =
  orderSlice.actions;
export default orderSlice.reducer;
