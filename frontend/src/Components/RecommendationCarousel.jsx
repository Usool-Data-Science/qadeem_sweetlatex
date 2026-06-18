import { useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";
import { HiSparkles } from "react-icons/hi2";
import { TbTrendingUp } from "react-icons/tb";
import { MdOutlineAutoAwesome } from "react-icons/md";
import {
  useGetForYouRecommendationsQuery,
  useGetSimilarItemsQuery,
  useGetTrendingQuery,
} from "../redux/features/recommendations/recommendationsApiSlice";
import { useLogInteractionMutation } from "../redux/features/interactions/interactionsApiSlice";

// ── Shared product card ────────────────────────────────────────────────────────

const RecommendedCard = ({ product, onView }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    onView(product.product_id);
    navigate(`/sales/${product.product_id}`);
  };

  return (
    <div
      onClick={handleClick}
      className="flex-shrink-0 w-44 sm:w-52 cursor-pointer group"
    >
      <div className="border border-zinc-700 hover:border-white transition-colors duration-200 overflow-hidden">
        {/* Image */}
        <div className="w-full h-52 sm:h-64 bg-zinc-900 overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-zinc-600 text-xs">
              No image
            </div>
          )}
        </div>

        {/* Details */}
        <div className="p-3 bg-black">
          <p className="text-white text-sm font-medium truncate">
            {product.title}
          </p>
          <p className="text-zinc-400 text-xs mt-1">£{product.price}</p>
          {product.is_sold_out && (
            <p className="text-red-500 text-xs mt-1">Sold out</p>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Skeleton loader ────────────────────────────────────────────────────────────

const SkeletonCard = () => (
  <div className="flex-shrink-0 w-44 sm:w-52 animate-pulse">
    <div className="border border-zinc-800">
      <div className="w-full h-52 sm:h-64 bg-zinc-800" />
      <div className="p-3 bg-black space-y-2">
        <div className="h-3 bg-zinc-800 rounded w-3/4" />
        <div className="h-3 bg-zinc-800 rounded w-1/3" />
      </div>
    </div>
  </div>
);

// ── Carousel shell ─────────────────────────────────────────────────────────────

const Carousel = ({ title, icon: Icon, products, isLoading, badge }) => {
  const scrollRef = useRef(null);

  const scroll = (dir) => {
    if (scrollRef.current) {
      scrollRef.current.scrollBy({
        left: dir === "left" ? -220 : 220,
        behavior: "smooth",
      });
    }
  };

  const { isAuthenticated } = useSelector((state) => state.auth);
  const [logInteraction] = useLogInteractionMutation();

  const handleView = (productId) => {
    // Fire-and-forget interaction log
    logInteraction({
      product: productId,
      interaction_type: "view",
      session_key: localStorage.getItem("session_key") || "",
      metadata: {},
    });
  };

  if (!isLoading && (!products || products.length === 0)) return null;

  return (
    <div className="my-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 px-1">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="text-white w-5 h-5" />}
          <h2 className="text-white text-lg font-medium tracking-wide">
            {title}
          </h2>
          {badge && (
            <span className="text-xs text-zinc-400 border border-zinc-700 px-2 py-0.5 rounded-full">
              {badge}
            </span>
          )}
        </div>

        {/* Scroll buttons */}
        <div className="flex gap-2">
          <button
            onClick={() => scroll("left")}
            className="p-1.5 border border-zinc-700 hover:border-white text-white transition-colors"
            aria-label="Scroll left"
          >
            <FiChevronLeft className="w-4 h-4" />
          </button>
          <button
            onClick={() => scroll("right")}
            className="p-1.5 border border-zinc-700 hover:border-white text-white transition-colors"
            aria-label="Scroll right"
          >
            <FiChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Scrollable row */}
      <div
        ref={scrollRef}
        className="flex gap-4 overflow-x-auto scrollbar-hide pb-2"
        style={{ scrollbarWidth: "none", msOverflowStyle: "none" }}
      >
        {isLoading
          ? Array.from({ length: 5 }).map((_, i) => <SkeletonCard key={i} />)
          : products.map((product) => (
              <RecommendedCard
                key={product.product_id}
                product={product}
                onView={handleView}
              />
            ))}
      </div>
    </div>
  );
};

// ── Exported components ────────────────────────────────────────────────────────

export const ForYouCarousel = () => {
  const { isAuthenticated } = useSelector((state) => state.auth);
  const { data, isLoading } = useGetForYouRecommendationsQuery(12);

  return (
    <Carousel
      title="For You"
      icon={HiSparkles}
      products={data?.results}
      isLoading={isLoading}
      badge={data?.strategy === "cold_start" ? "Trending picks" : undefined}
    />
  );
};

export const TrendingCarousel = () => {
  const { data, isLoading } = useGetTrendingQuery(12);

  return (
    <Carousel
      title="Trending Now"
      icon={TbTrendingUp}
      products={data?.results}
      isLoading={isLoading}
    />
  );
};

export const SimilarItemsCarousel = ({ productId }) => {
  const { data, isLoading } = useGetSimilarItemsQuery(
    { productId, top_k: 12 },
    { skip: !productId },
  );

  return (
    <Carousel
      title="You Might Also Like"
      icon={MdOutlineAutoAwesome}
      products={data?.results}
      isLoading={isLoading}
    />
  );
};
