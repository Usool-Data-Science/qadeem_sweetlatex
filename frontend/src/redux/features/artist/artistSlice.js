import { createSlice } from "@reduxjs/toolkit";

const initialState = {
  selectedArtist: null,
  filterCategory: "ALL", // For the Archive/Collaboration page
};

const artistSlice = createSlice({
  name: "artist",
  initialState,
  reducers: {
    setSelectedArtist: (state, action) => {
      state.selectedArtist = action.payload;
    },
    setArtistFilter: (state, action) => {
      state.filterCategory = action.payload;
    },
    clearArtistState: (state) => {
      state.selectedArtist = null;
      state.filterCategory = "ALL";
    },
  },
});

export const { setSelectedArtist, setArtistFilter, clearArtistState } =
  artistSlice.actions;

export default artistSlice.reducer;
