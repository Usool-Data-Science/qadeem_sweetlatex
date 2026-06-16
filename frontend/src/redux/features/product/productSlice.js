import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  searchTerm: "",
  filters: {
    color: null,
    style: null,
    minPrice: 0,
    maxPrice: 1000,
  },
  sortBy: "newest",
};

const productSlice = createSlice({
  name: "products",
  initialState,
  reducers: {
    setSearchTerm: (state, action) => {
      state.searchTerm = action.payload;
    },
    setFilter: (state, action) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    resetFilters: (state) => {
      state.filters = initialState.filters;
      state.searchTerm = "";
    },
    setSortBy: (state, action) => {
      state.sortBy = action.payload;
    },
  },
});

export const { setSearchTerm, setFilter, resetFilters, setSortBy } =
  productSlice.actions;
export default productSlice.reducer;
