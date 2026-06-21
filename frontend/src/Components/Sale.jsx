import ProgressBar from "./ProgressBar";
import Body from "./Body";
import Carousel from "./Carousel";
import { useNavigate, useParams } from "react-router-dom";
import { useState } from "react";
import { useSelector } from "react-redux";
import { toast } from "sonner";
import { useGetProductDetailsQuery } from "../redux/features/product/productApiSlice";
import {
  useAddToCartMutation,
  useGetCartQuery,
} from "../redux/features/cart/cartApiSlice";
import { useRetrieveUserQuery } from "../redux/features/auth/authApiSlice";
import { useLogInteractionMutation } from "../redux/features/interactions/interactionsApiSlice";
import { SimilarItemsCarousel } from "./RecommendationCarousel";

const Sale = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [selectedSize, setSelectedSize] = useState("");
  const [selectedQuantity, setSelectedQuantity] = useState(1);

  const { isAuthenticated } = useSelector((state) => state.auth);

  // ── data fetching ──────────────────────────────────────────────────────────
  const { data: product, isLoading, isError } = useGetProductDetailsQuery(id);

  // Fixed: skip when not authenticated — prevents 401 console noise
  const { data: user } = useRetrieveUserQuery(undefined, {
    skip: !isAuthenticated,
  });

  const { data: cart } = useGetCartQuery(undefined, { skip: !user });

  const [addToCart] = useAddToCartMutation();
  const [logInteraction] = useLogInteractionMutation();

  const productCountInCart =
    cart?.items?.find((item) => item.product_id === id)?.quantity ?? 0;

  // Log a CLICK interaction when the product page loads
  // useEffect equivalent: log once when product data arrives
  const [clickLogged, setClickLogged] = useState(false);
  if (product && !clickLogged) {
    setClickLogged(true);
    logInteraction({
      product: id,
      interaction_type: "click",
      session_key: localStorage.getItem("session_key") || "",
      metadata: {},
    });
  }

  // ── unified availability logic ─────────────────────────────────────────────
  const isExpired = product?.is_expired;
  const isSoldOut = product?.is_sold_out || product?.quantity === 0;
  const isUnavailable = isExpired || isSoldOut;
  const isAvailableForPreorder = !isUnavailable;

  // ── handlers ──────────────────────────────────────────────────────────────
  const handleSize = (e) => {
    e.preventDefault();
    setSelectedSize(e.target.textContent);
  };

  const handlePreorder = async (e) => {
    e.preventDefault();

    if (isUnavailable) {
      toast.error("This product is no longer available.");
      return;
    }

    if (!selectedSize) {
      toast.error("Please pick a size first!");
      return;
    }

    if (selectedQuantity > product.total_in_stock) {
      toast.error(`Only ${product.total_in_stock} items left in stock`);
      return;
    }

    try {
      await addToCart({
        product_id: product.product_id,
        size: selectedSize,
        quantity: Number(selectedQuantity),
      }).unwrap();

      toast.success("Added to cart!");
    } catch (err) {
      toast.error("Failed to add to cart. Please try again.");
    }
  };

  // ── render states ──────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <Body>
        <span className="loading loading-ring loading-lg"></span>
      </Body>
    );
  }

  if (isError || !product) {
    return (
      <Body>
        <p className="text-center text-white">Product not found.</p>
      </Body>
    );
  }

  return (
    <Body>
      <div className="bg-inherit mt-4 px-2 sm:px-4">
        <div className="lg:m-10 border border-gray-100 p-4 flex flex-col lg:flex-row gap-2 items-center sm:items-start justify-between lg:mx-16 xl:mx-32">
          {/* Title and Artist name for iphone screens */}
          <div className="flex flex-col justify-center items-center sm:hidden font-courier">
            <p className="whitespace-nowrap text-xl">{product.title}</p>
            <p className="text-xl whitespace-nowrap">X</p>
            <p className="text-xl whitespace-nowrap">{product.artist_name}</p>
          </div>

          {/* Image + Carousel */}
          <div className="w-full lg:w-[60%] flex flex-col gap-4">
            <Carousel subImages={product.images} />

            <p className="sm:hidden font-courier">
              {product.artist_details?.length >= 500 ? (
                <>
                  {product.artist_details.slice(0, 500)}
                  <label htmlFor="moreDetails" className="bg-gray-600 ml-4">
                    more...
                  </label>
                </>
              ) : (
                product.artist_details || "Details not available"
              )}
            </p>

            {/* Progress */}
            {isAvailableForPreorder && product.days_left > 0 && (
              <>
                <p className="text-center text-white font-courier sm:hidden">
                  Pre-order only {product.goal} days
                </p>

                <div className="flex flex-col">
                  <p className="flex justify-between text-white text-sm">
                    <span className="hidden sm:block max-w-[50%]">
                      Pre-order only {product.goal} days
                    </span>
                    <span className="hidden sm:block max-w-[50%] text-right">
                      -{product.days_left} Days
                    </span>
                  </p>

                  <ProgressBar
                    daysLeft={product.days_left}
                    deadLine={product.deadline}
                  />
                </div>
              </>
            )}
          </div>

          {/* Details */}
          <div className="sm:mx-9 lg:w-[30%] flex flex-col gap-4 font-courier">
            <div className="hidden sm:flex sm:flex-col md:flex-row lg:flex-col justify-center items-center gap-1">
              <p className="whitespace-nowrap lg:text-lg">
                {product.title?.charAt(0).toUpperCase() +
                  product.title?.slice(1).toLowerCase()}
              </p>
              <p className="lg:text-lg p-4">X</p>
              <p className="lg:text-lg whitespace-nowrap">
                {product.artist_name}
              </p>
            </div>

            <p className="hidden sm:block">
              {product.artist_details?.length >= 500 ? (
                <>
                  {product.artist_details.slice(0, 500)}
                  <label htmlFor="moreDetails" className="bg-gray-600 ml-4">
                    more...
                  </label>
                </>
              ) : (
                product.artist_details || "Details not available"
              )}
            </p>

            <a
              href={product.artist_website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-base break-all"
            >
              {product.artist_website}
            </a>

            {/* ── PRODUCT AVAILABLE SECTION ────────────────────────── */}
            {isAvailableForPreorder ? (
              <>
                <p>Composition: {product.composition}</p>
                <p>Color: {product.color}</p>

                <button
                  className="self-start"
                  onClick={() =>
                    document.getElementById("sizeGuideModal").showModal()
                  }
                >
                  Size guide +
                </button>

                <p>Size</p>

                <div className="flex gap-4">
                  {product?.available_sizes?.map((size) => (
                    <button
                      key={size}
                      onClick={handleSize}
                      className={`text-lg w-8 min-w-fit grid place-content-center border-2 transition-all 
                        ${
                          selectedSize === size
                            ? "scale-105 bg-gray-800 bg-white text-black"
                            : "text-white bg-transparent"
                        }`}
                    >
                      {size.toUpperCase()}
                    </button>
                  ))}
                </div>

                <p>Quantity</p>

                <div className="flex items-center gap-2">
                  <input
                    className="bg-white p-1 text-sm text-black w-10 max-w-fit text-center"
                    type="number"
                    value={selectedQuantity}
                    onChange={(e) => {
                      const value = Number(e.target.value);
                      if (!value) {
                        setSelectedQuantity(1);
                        return;
                      }
                      setSelectedQuantity(
                        Math.max(Math.min(product.total_in_stock, value)),
                      );
                    }}
                  />
                </div>

                <p>Price: {product.price} €</p>

                <button
                  className="
                    border border-gray-200 px-4 py-2 w-fit
                    hover:bg-white hover:text-black hover:font-bold
                    transition-all duration-200
                    disabled:opacity-40
                    disabled:cursor-not-allowed
                    disabled:hover:bg-transparent
                    disabled:hover:text-gray-200
                    disabled:hover:font-normal
                  "
                  onClick={handlePreorder}
                  disabled={
                    isUnavailable ||
                    selectedQuantity > product.total_in_stock ||
                    !selectedSize
                  }
                >
                  PRE-ORDER
                </button>

                <p>
                  Shipping in approximately 4 weeks after the end of the sale.
                </p>
              </>
            ) : (
              <p className="text-red-600 font-courier text-xl">
                Sales has ended
              </p>
            )}
          </div>
        </div>

        {/* ── Similar Items Carousel ────────────────────────────────────────── */}
        {/* Rendered below the product detail panel — queries CLIP/FAISS */}
        <div className="lg:mx-10 mt-8">
          <SimilarItemsCarousel productId={id} />
        </div>
      </div>

      {/* More details modal */}
      <input type="checkbox" id="moreDetails" className="modal-toggle" />
      <div className="modal m-5" role="dialog">
        <div className="modal-box bg-black">
          <h3 className="text-lg">Detail about {product.artist_name}</h3>
          <p className="py-4">{product.artist_details}</p>
          <div className="modal-action">
            <label htmlFor="moreDetails" className="btn">
              Close!
            </label>
          </div>
        </div>
      </div>

      {/* Size guide */}
      <dialog id="sizeGuideModal" className="modal">
        <div className="modal-box bg-black relative">
          <form method="dialog">
            <button className="absolute right-4 top-4 text-white text-2xl hover:text-gray-300">
              ✕
            </button>
          </form>
          <img
            className="w-full object-contain max-h-[480px]"
            src="/images/sizeGuide.jpg"
            alt="Size Guide"
          />
        </div>
        <form method="dialog" className="modal-backdrop">
          <button>close</button>
        </form>
      </dialog>
    </Body>
  );
};

export default Sale;
