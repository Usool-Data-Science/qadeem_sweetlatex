import React, { useState } from "react";
import Body from "../Components/Body";
import { useNavigate } from "react-router-dom";
import useAuth from "../hooks/use-auth";
import { useGetMyOrdersQuery } from "../redux/features/order/orderApiSlice";

const AccountPage = () => {
  const { user } = useAuth();
  const { data: orders, isLoading } = useGetMyOrdersQuery();
  const navigate = useNavigate();
  const [expandedOrders, setExpandedOrders] = useState({});

  const toggleOrder = (orderId) => {
    setExpandedOrders((prev) => ({
      ...prev,
      [orderId]: !prev[orderId],
    }));
  };

  const defaultAddress =
    user?.addresses?.find((a) => a.is_default) || user?.addresses?.[0] || null;

  if (!user) {
    return (
      <Body className="font-courier">
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-4 py-10">
          <div className="mx-auto max-w-2xl rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 p-10 text-center">
            <h1 className="text-3xl md:text-4xl font-bold text-white tracking-tight">
              My Account
            </h1>
            <p className="mt-4 text-slate-400 text-base md:text-lg">
              Please log in to view your account details.
            </p>
            <button
              onClick={() => navigate("/login")}
              className="mt-8 rounded-xl bg-white px-6 py-3 text-sm font-semibold text-slate-900 transition-all duration-200 hover:scale-[1.02] hover:bg-slate-100"
            >
              Go to Login
            </button>
          </div>
        </div>
      </Body>
    );
  }

  return (
    <Body>
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-4 py-10 font-courier">
        <div className="mx-auto max-w-5xl space-y-8">
          {/* HEADER */}
          <div className="text-center">
            <h1 className="text-3xl md:text-4xl font-bold tracking-tight text-white">
              My Account
            </h1>
            <p className="mt-3 text-sm md:text-base text-slate-400">
              Manage your orders and personal information.
            </p>
          </div>

          {/* MAIN GRID */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* ORDERS */}
            <div className="lg:col-span-2 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30">
              <div className="border-b border-slate-800 px-6 py-5">
                <h2 className="text-xl font-semibold text-white font-courier">
                  Order History
                </h2>
                <p className="mt-1 text-sm text-slate-400">
                  View and track your recent purchases.
                </p>
              </div>

              <div className="p-6">
                {orders?.length > 0 ? (
                  <ul className="space-y-6">
                    {orders?.map((order) => {
                      const firstProduct = order.items[0];
                      const remainingProducts = order.items.slice(1);
                      const isExpanded = expandedOrders[order.order_id];

                      return (
                        <li
                          key={order.order_id}
                          className="rounded-2xl border border-slate-800 bg-slate-950/40 overflow-hidden"
                        >
                          <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
                            <div>
                              <p className="text-sm text-slate-400">
                                Order Date
                              </p>
                              <p className="text-white font-medium">
                                {new Date(
                                  order.created_at,
                                ).toLocaleDateString()}
                              </p>
                            </div>
                            <button
                              onClick={() =>
                                navigate(`/orders/${order.order_id}`)
                              }
                              className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800"
                            >
                              View Order
                            </button>
                          </div>

                          <div
                            className="flex gap-4 p-5 cursor-pointer transition hover:bg-slate-800/40"
                            onClick={() =>
                              navigate(`/orders/${order.order_id}`)
                            }
                          >
                            <img
                              src={firstProduct.product_image}
                              alt={firstProduct.product_name}
                              className="h-24 w-20 rounded-lg object-cover border border-slate-700"
                            />
                            <div className="flex flex-col justify-center">
                              <p className="text-white font-medium">
                                {firstProduct.product_name}
                              </p>
                              <p className="mt-1 text-sm text-slate-400">
                                ${firstProduct.price}
                              </p>
                            </div>
                          </div>

                          {remainingProducts.length > 0 && (
                            <div className="px-5 pb-4">
                              <button
                                onClick={() => toggleOrder(order.order_id)}
                                className="text-sm font-medium text-slate-300 hover:text-white transition"
                              >
                                {isExpanded
                                  ? "Hide additional items"
                                  : `+ ${remainingProducts.length} more item(s)`}
                              </button>
                            </div>
                          )}

                          {isExpanded && (
                            <div className="border-t border-slate-800">
                              {remainingProducts.map((product) => (
                                <div
                                  key={product.id}
                                  className="flex gap-4 p-5 cursor-pointer transition hover:bg-slate-800/40"
                                  onClick={() =>
                                    navigate(`/orders/${order.order_id}`)
                                  }
                                >
                                  <img
                                    src={product.product_image}
                                    alt={product.product_name}
                                    className="h-24 w-20 rounded-lg object-cover border border-slate-700"
                                  />
                                  <div className="flex flex-col justify-center">
                                    <p className="text-white font-medium">
                                      {product.product_name}
                                    </p>
                                    <p className="mt-1 text-sm text-slate-400">
                                      ${product.price}
                                    </p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-700 p-10 text-center">
                    <p className="text-slate-400">You have no orders yet.</p>
                  </div>
                )}
              </div>
            </div>

            {/* RIGHT COLUMN */}
            <div className="space-y-6">
              {/* CONTACT DETAILS */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30">
                <div className="border-b border-slate-800 px-6 py-5">
                  <h2 className="text-xl font-semibold text-white">
                    Contact Details
                  </h2>
                  <p className="mt-1 text-sm text-slate-400">
                    Your personal account information.
                  </p>
                </div>

                <div className="p-6 space-y-4">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Full Name
                    </p>
                    <p className="mt-1 text-white">
                      {user.first_name} {user.last_name}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Email
                    </p>
                    <p className="mt-1 text-white">{user.email}</p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500">
                      Phone
                    </p>
                    <p className="mt-1 text-white">
                      {user.phone_number || "—"}
                    </p>
                  </div>

                  <button
                    className="w-full rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition-all duration-200 hover:scale-[1.02] hover:bg-slate-100"
                    onClick={() => navigate("/editUser")}
                  >
                    Edit Details
                  </button>
                </div>
              </div>

              {/* ADDRESSES */}
              <div className="rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30">
                <div className="border-b border-slate-800 px-6 py-5 flex items-center justify-between">
                  <div>
                    <h2 className="text-xl font-semibold text-white">
                      Addresses
                    </h2>
                    <p className="mt-1 text-sm text-slate-400">
                      Your saved delivery addresses.
                    </p>
                  </div>
                  <button
                    onClick={() =>
                      navigate("/editUser", { state: { tab: "address" } })
                    }
                    className="text-xs text-slate-400 hover:text-white transition border border-slate-700 rounded-lg px-3 py-1.5 hover:border-slate-500"
                  >
                    + Add
                  </button>
                </div>

                <div className="p-6 space-y-3">
                  {user.addresses?.length > 0 ? (
                    user.addresses.map((addr) => (
                      <div
                        key={addr.id}
                        className={`rounded-xl border px-4 py-3 transition ${
                          addr.is_default
                            ? "border-slate-600 bg-slate-800/50"
                            : "border-slate-800 bg-slate-950/30"
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold uppercase tracking-wide text-slate-400 border border-slate-700 rounded px-1.5 py-0.5 capitalize">
                              {addr.address_type}
                            </span>
                            {addr.is_default && (
                              <span className="text-xs font-medium text-white bg-slate-600 rounded px-1.5 py-0.5">
                                Default
                              </span>
                            )}
                          </div>
                          <button
                            onClick={() =>
                              navigate("/editUser", {
                                state: {
                                  tab: "address",
                                  type: addr.address_type,
                                },
                              })
                            }
                            className="text-xs text-slate-500 hover:text-white transition"
                          >
                            Edit
                          </button>
                        </div>
                        <p className="text-sm text-white">{addr.street}</p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {addr.city}, {addr.state}, {addr.country}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="rounded-xl border border-dashed border-slate-700 p-6 text-center">
                      <p className="text-sm text-slate-500">
                        No addresses saved yet.
                      </p>
                      <button
                        onClick={() =>
                          navigate("/editUser", { state: { tab: "address" } })
                        }
                        className="mt-3 text-xs text-slate-400 hover:text-white transition"
                      >
                        + Add your first address
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Body>
  );
};

export default AccountPage;
