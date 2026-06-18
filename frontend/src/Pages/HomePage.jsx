import { useState } from "react";
import { TbCameraSearch } from "react-icons/tb";
import Body from "../Components/Body";
import useProduct from "../hooks/use-product";
import GeneralPage from "./GeneralPage";
import {
  ForYouCarousel,
  TrendingCarousel,
} from "../Components/RecommendationCarousel";
import VisualSearchModal from "../Components/VisualSearchModal";

const HomePage = () => {
  const { products, isLoading } = useProduct();
  const [visualSearchOpen, setVisualSearchOpen] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <span className="loading loading-ring loading-lg" />
      </div>
    );
  }

  return (
    <Body search>
      {/* Visual search trigger */}
      <div className="flex justify-end px-1 mb-2">
        <button
          onClick={() => setVisualSearchOpen(true)}
          className="flex items-center gap-2 text-zinc-400 hover:text-white text-sm border border-zinc-700 hover:border-white px-3 py-1.5 transition-colors"
        >
          <TbCameraSearch className="w-4 h-4" />
          Visual Search
        </button>
      </div>

      {/* Personalised recommendations */}
      <ForYouCarousel />

      {/* Main product listing */}
      <GeneralPage products={products?.products} />

      {/* Trending section below main listing */}
      <TrendingCarousel />

      {/* Visual search modal */}
      <VisualSearchModal
        isOpen={visualSearchOpen}
        onClose={() => setVisualSearchOpen(false)}
      />
    </Body>
  );
};

export default HomePage;
