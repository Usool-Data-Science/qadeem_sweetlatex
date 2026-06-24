import { useEffect, useState } from "react";
import Body from "../Components/Body";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import useAuth from "../hooks/use-auth";
import {
  useGetCartQuery,
  useUpdateCartItemMutation,
  useRemoveFromCartMutation,
  useCheckoutMutation,
} from "../redux/features/cart/cartApiSlice";
import { getErrorMessage } from "../utils";

const Cart = () => {
  const { user, loadingUser } = useAuth();
  const navigate = useNavigate();
  const [isCheckingOut, setIsCheckingOut] = useState(false);

  // fetch cart from backend — skip if user not loaded yet
  const { data: cart, isLoading: isCartLoading } = useGetCartQuery(undefined, {
    skip: !user, // don't fetch cart if not logged in
  });

  const [updateCartItem] = useUpdateCartItemMutation();
  const [removeFromCart] = useRemoveFromCartMutation();
  const [checkout] = useCheckoutMutation();

  // derive these from backend response instead of tracking locally
  const userCart = cart?.items ?? [];
  const totalPrice = cart?.total_price ?? 0;

  // redirect if not authenticated
  useEffect(() => {
    if (!loadingUser && !user) {
      toast("Please login first!");
      navigate("/login");
    }
  }, [user, loadingUser, navigate]);

  // redirect to Stripe checkout URL
  const handleOrder = async (e) => {
    e.preventDefault();
    setIsCheckingOut(true);
    try {
      const result = await checkout().unwrap();
      if (result?.session_url) {
        window.location.href = result.session_url;
      } else if (result?.cancel_url) {
        window.location.href = result.cancel_url;
      }
    } catch (error) {
      toast.error(getErrorMessage(error));
    } finally {
      setIsCheckingOut(false);
    }
  };

  const handleIncrement = async (item_id) => {
    try {
      await updateCartItem({ item_id, action: "incr" }).unwrap();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleDecrement = async (item_id) => {
    try {
      await updateCartItem({ item_id, action: "decr" }).unwrap();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  const handleRemove = async (item_id) => {
    try {
      await removeFromCart(item_id).unwrap();
    } catch (error) {
      toast.error(getErrorMessage(error));
    }
  };

  // show loading while auth is being determined
  if (loadingUser || isCartLoading) {
    return <span className="loading loading-ring loading-lg"></span>;
  }

  // don't render anything if not logged in — useEffect handles redirect
  if (!user) return null;

  return (
    <Body>
      <div
        className="min-h-screen p-8 font-courier"
        style={{ backgroundColor: "#000" }}
      >
        <div className="container mx-auto">
          <div className="grid grid-cols-1 gap-4 border p-4 sm:mx-24 lg:mx-64">
            <h1 className="text-3xl text-white font-courier text-center">
              Your Cart
            </h1>

            {userCart.length === 0 ? (
              <p className="text-center text-white">Your cart is empty.</p>
            ) : (
              <div className="lg:col-span-2 bg-wh shadow-md rounded-lg p-6 pt-2">
                <div className="space-y-4">
                  {userCart.map((item) => (
                    <div
                      key={item.id}
                      className="flex items-center justify-between border-b py-4"
                    >
                      <div className="flex items-center space-x-4 w-full gap-2 sm:gap-8 lg:gap-12">
                        <img
                          src={item.product_image || "default-image.png"}
                          alt={item.product_name}
                          className="w-16 h-16 object-cover"
                        />
                        <div className="flex-grow flex flex-col gap-4 justify-end">
                          <div className="flex justify-between gap-8 items-center">
                            <p className="text-white">
                              {item.product_name} ({item.size})
                            </p>
                            <button
                              className="border border-gray-50 bg-transparent p-1 h-4 w-4 grid place-content-center"
                              onClick={() => handleRemove(item.id)}
                            >
                              x
                            </button>
                          </div>
                          <div className="flex justify-between gap-8">
                            <div className="flex items-center gap-2">
                              <button onClick={() => handleDecrement(item.id)}>
                                -
                              </button>
                              <p>{item.quantity}</p>
                              <button onClick={() => handleIncrement(item.id)}>
                                +
                              </button>
                            </div>
                            <p className="text-sm text-white">
                              {item.product_price} €
                            </p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}

                  <div className="flex justify-between text-white">
                    <span>Subtotal</span>
                    <span>{totalPrice} €</span>
                  </div>

                  <button
                    className="border border-gray-50 hover:text-red-500 p-1 font-courier w-full mt-6"
                    onClick={handleOrder}
                    disabled={userCart.length === 0 || isCheckingOut}
                    aria-busy={isCheckingOut}
                  >
                    {isCheckingOut ? (
                      <progress className="progress text-slate-200"></progress>
                    ) : (
                      "Checkout"
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Order Summary */}
            {/* <div className="bg-white text-gray-600 shadow-md rounded-lg p-6">
              <h2 className="text-xl font-bold mb-4">Order Summary</h2>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="font-bold">{totalPrice.toFixed(2)} €</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Shipping</span>
                  <span className="font-bold">Free</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Tax</span>
                  <span className="font-bold">
                    {(totalPrice * 0.1).toFixed(2)} €
                  </span>
                </div>
              </div>
              <hr className="my-4" />
              <div className="flex justify-between">
                <span className="text-xl font-bold">Total</span>
                <span className="text-xl font-bold">
                  {(totalPrice + totalPrice * 0.1).toFixed(2)} €
                </span>
              </div>
              <button
                className="btn btn-primary w-full mt-6"
                onClick={handleOrder}
                disabled={userCart.length === 0 || isCheckingOut}
                aria-busy={isCheckingOut}
              >
                {isCheckingOut ? (
                  <progress className="progress text-slate-200"></progress>
                ) : (
                  "Checkout"
                )}
              </button>
            </div> */}
          </div>
        </div>
      </div>
    </Body>
  );
};

export default Cart;
