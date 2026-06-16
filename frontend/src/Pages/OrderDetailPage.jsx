import React, { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Body from "../Components/Body";
import { useGetOrderDetailsQuery } from "../redux/features/order/orderApiSlice";

/* ─── Status config ─── */
const STATUS_CONFIG = {
  pending: {
    label: "Pending",
    color: "text-amber-400",
    bg: "bg-amber-400/10 border-amber-400/30",
    dot: "bg-amber-400",
    step: 0,
  },
  confirmed: {
    label: "Confirmed",
    color: "text-sky-400",
    bg: "bg-sky-400/10 border-sky-400/30",
    dot: "bg-sky-400",
    step: 1,
  },
  processing: {
    label: "Processing",
    color: "text-violet-400",
    bg: "bg-violet-400/10 border-violet-400/30",
    dot: "bg-violet-400",
    step: 2,
  },
  shipped: {
    label: "Shipped",
    color: "text-indigo-400",
    bg: "bg-indigo-400/10 border-indigo-400/30",
    dot: "bg-indigo-400",
    step: 3,
  },
  delivered: {
    label: "Delivered",
    color: "text-emerald-400",
    bg: "bg-emerald-400/10 border-emerald-400/30",
    dot: "bg-emerald-400",
    step: 4,
  },
  cancelled: {
    label: "Cancelled",
    color: "text-rose-400",
    bg: "bg-rose-400/10 border-rose-400/30",
    dot: "bg-rose-400",
    step: -1,
  },
};

const TIMELINE_STEPS = [
  {
    key: "confirmed",
    label: "Order Confirmed",
    desc: "Your order has been received",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
        <path
          fillRule="evenodd"
          d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    key: "processing",
    label: "Processing",
    desc: "Items are being prepared",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
        <path
          fillRule="evenodd"
          d="M15.312 11.424a5.5 5.5 0 01-9.201 2.466l-.312-.311h2.433a.75.75 0 000-1.5H3.989a.75.75 0 00-.75.75v4.242a.75.75 0 001.5 0v-2.43l.31.31a7 7 0 0011.712-3.138.75.75 0 00-1.449-.39zm1.23-3.723a.75.75 0 00.219-.53V2.929a.75.75 0 00-1.5 0V5.36l-.31-.31A7 7 0 003.239 8.188a.75.75 0 101.448.389A5.5 5.5 0 0113.89 6.11l.311.31h-2.432a.75.75 0 000 1.5h4.243a.75.75 0 00.53-.219z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
  {
    key: "shipped",
    label: "Shipped",
    desc: "Your order is on the way",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
        <path d="M6.5 3c-1.051 0-2.093.04-3.125.117A1.49 1.49 0 002 4.607V10.5h9V4.606c0-.771-.59-1.43-1.375-1.489A41.3 41.3 0 006.5 3zM2 12v2.5A1.5 1.5 0 003.5 16h.041a3 3 0 005.918 0h.791a3 3 0 005.918 0h.33A1.5 1.5 0 0018 14.5V12H2zM13 11.5V4.64c.37.031.74.065 1.107.101A1.5 1.5 0 0115.5 6.3v5.2H13z" />
      </svg>
    ),
  },
  {
    key: "delivered",
    label: "Delivered",
    desc: "Order delivered successfully",
    icon: (
      <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
        <path
          fillRule="evenodd"
          d="M9.664 1.319a.75.75 0 01.672 0 41.059 41.059 0 018.198 5.424.75.75 0 01-.254 1.285 31.372 31.372 0 00-7.86 3.83.75.75 0 01-.84 0 31.508 31.508 0 00-2.08-1.287V9.394c0-.244.116-.463.302-.592a35.504 35.504 0 013.305-2.033.75.75 0 00-.714-1.319 37 37 0 00-3.446 2.12A2.216 2.216 0 006 9.393v.38a31.293 31.293 0 00-4.28-1.746.75.75 0 01-.254-1.285 41.059 41.059 0 018.198-5.424zM6 11.459a29.848 29.848 0 00-2.455-1.158 41.029 41.029 0 00-.39 3.114.75.75 0 00.419.74c.528.256 1.046.53 1.554.82-.21.324-.455.63-.739.914a.75.75 0 101.06 1.06c.37-.369.69-.77.96-1.193a26.61 26.61 0 013.095 2.348.75.75 0 00.992 0 26.547 26.547 0 015.93-3.95.75.75 0 00.42-.739 41.053 41.053 0 00-.39-3.114 29.925 29.925 0 00-5.199 2.801 2.25 2.25 0 01-2.514 0c-.41-.275-.826-.541-1.25-.796zM8.282 17.98a.75.75 0 00-.314-1.465 25.236 25.236 0 00-3.038 1.327.75.75 0 00.77 1.29 23.73 23.73 0 012.582-1.152zM10 5.5a.75.75 0 01.75.75v2.5a.75.75 0 01-1.5 0v-2.5A.75.75 0 0110 5.5z"
          clipRule="evenodd"
        />
      </svg>
    ),
  },
];

/* ─── Skeleton loader ─── */
const Skeleton = ({ className }) => (
  <div className={`animate-pulse rounded bg-slate-800/60 ${className}`} />
);

/* ─── Main Component ─── */
const OrderDetailPage = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const { data: order, isLoading, isError } = useGetOrderDetailsQuery(orderId);

  const statusKey = order?.status?.toLowerCase() || "pending";
  const statusCfg = STATUS_CONFIG[statusKey] || STATUS_CONFIG.pending;
  const currentStep = statusCfg.step;

  const subtotal = order?.items?.reduce(
    (acc, item) => acc + parseFloat(item.price) * item.quantity,
    0,
  );
  const shipping = 0; // adjust if your API returns shipping cost
  const total = order?.total_price ?? subtotal;

  /* ─── Loading state ─── */
  if (isLoading) {
    return (
      <Body>
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-4 py-10 font-courier">
          <div className="mx-auto max-w-4xl space-y-6">
            <Skeleton className="h-8 w-48" />
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 space-y-4">
                <Skeleton className="h-48 w-full rounded-2xl" />
                <Skeleton className="h-32 w-full rounded-2xl" />
              </div>
              <div className="space-y-4">
                <Skeleton className="h-40 w-full rounded-2xl" />
                <Skeleton className="h-32 w-full rounded-2xl" />
              </div>
            </div>
          </div>
        </div>
      </Body>
    );
  }

  /* ─── Error state ─── */
  if (isError || !order) {
    return (
      <Body>
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center px-4 font-courier">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl p-10 text-center max-w-md w-full">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-rose-500/10 border border-rose-500/20">
              <svg
                viewBox="0 0 20 20"
                fill="currentColor"
                className="w-6 h-6 text-rose-400"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-white">
              Order Not Found
            </h2>
            <p className="mt-2 text-sm text-slate-400">
              We couldn't retrieve this order. It may have been removed or the
              ID is invalid.
            </p>
            <button
              onClick={() => navigate("/account")}
              className="mt-6 w-full rounded-xl bg-white px-5 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
            >
              Back to Account
            </button>
          </div>
        </div>
      </Body>
    );
  }

  return (
    <Body>
      <style>{`
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .fade-up { animation: fadeUp 0.45s ease both; }
        .fade-up-1 { animation-delay: 0.05s; }
        .fade-up-2 { animation-delay: 0.12s; }
        .fade-up-3 { animation-delay: 0.19s; }
        .fade-up-4 { animation-delay: 0.26s; }
        .fade-up-5 { animation-delay: 0.33s; }

        .step-line::after {
          content: '';
          position: absolute;
          left: 50%;
          top: 100%;
          transform: translateX(-50%);
          width: 2px;
          height: 2rem;
          background: linear-gradient(to bottom, currentColor, transparent);
          opacity: 0.3;
        }
      `}</style>

      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 px-4 py-10 font-courier">
        <div className="mx-auto max-w-4xl space-y-8">
          {/* ── Back + Header ── */}
          <div className="fade-up fade-up-1 flex items-start justify-between gap-4 flex-wrap">
            <div>
              <button
                onClick={() => navigate("/account")}
                className="inline-flex items-center gap-1.5 text-sm text-slate-400 hover:text-white transition mb-3"
              >
                <svg
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  className="w-4 h-4"
                >
                  <path
                    fillRule="evenodd"
                    d="M17 10a.75.75 0 01-.75.75H5.612l4.158 3.96a.75.75 0 11-1.04 1.08l-5.5-5.25a.75.75 0 010-1.08l5.5-5.25a.75.75 0 111.04 1.08L5.612 9.25H16.25A.75.75 0 0117 10z"
                    clipRule="evenodd"
                  />
                </svg>
                Back to Account
              </button>
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                Order Details
              </h1>
              <p className="mt-1 text-sm text-slate-400 font-mono tracking-wide">
                #{order.order_id.split("-")[0].toUpperCase()}
                <span className="text-slate-600"> · </span>
                {new Date(order.created_at).toLocaleDateString("en-US", {
                  weekday: "short",
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>

            {/* Status badge */}
            <div
              className={`inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold ${statusCfg.bg} ${statusCfg.color}`}
            >
              <span
                className={`h-2 w-2 rounded-full ${statusCfg.dot} animate-pulse`}
              />
              {statusCfg.label}
            </div>
          </div>

          {/* ── Main grid ── */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* LEFT: Items + Timeline */}
            <div className="lg:col-span-2 space-y-6">
              {/* Order Items */}
              <div className="fade-up fade-up-2 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 overflow-hidden">
                <div className="border-b border-slate-800 px-6 py-5 flex items-center justify-between">
                  <div>
                    <h2 className="text-base font-semibold text-white">
                      Items Ordered
                    </h2>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {order.items.length}{" "}
                      {order.items.length === 1 ? "item" : "items"} in this
                      order
                    </p>
                  </div>
                  <span className="text-xs text-slate-500 border border-slate-700 rounded-lg px-3 py-1.5 font-mono">
                    {order.items.length}{" "}
                    {order.items.length === 1 ? "product" : "products"}
                  </span>
                </div>

                <ul className="divide-y divide-slate-800/70">
                  {order.items.map((item, idx) => (
                    <li
                      key={item.id}
                      className="flex gap-4 px-6 py-5 transition hover:bg-slate-800/20"
                    >
                      {/* Product image */}
                      <div className="relative flex-shrink-0">
                        {item.product_image ? (
                          <img
                            src={item.product_image}
                            alt={item.product_name}
                            className="h-24 w-20 rounded-xl object-cover border border-slate-700"
                          />
                        ) : (
                          <div className="h-24 w-20 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center">
                            <svg
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              className="w-8 h-8 text-slate-600"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={1.5}
                                d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 0 0 1.5-1.5V6a1.5 1.5 0 0 0-1.5-1.5H3.75A1.5 1.5 0 0 0 2.25 6v12a1.5 1.5 0 0 0 1.5 1.5Zm10.5-11.25h.008v.008h-.008V8.25Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z"
                              />
                            </svg>
                          </div>
                        )}
                        {/* Quantity badge */}
                        {item.quantity > 1 && (
                          <span className="absolute -top-2 -right-2 h-5 w-5 rounded-full bg-white text-slate-900 text-xs font-bold flex items-center justify-center">
                            {item.quantity}
                          </span>
                        )}
                      </div>

                      {/* Info */}
                      <div className="flex flex-1 flex-col justify-center min-w-0">
                        <p className="text-white font-medium truncate">
                          {item.product_name}
                        </p>
                        <div className="mt-1.5 flex flex-wrap items-center gap-2">
                          {item.size_name && (
                            <span className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800/50 px-2 py-0.5 text-xs text-slate-300">
                              Size:{" "}
                              <strong className="text-white">
                                {item.size_name}
                              </strong>
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1 rounded-md border border-slate-700 bg-slate-800/50 px-2 py-0.5 text-xs text-slate-300">
                            Qty:{" "}
                            <strong className="text-white">
                              {item.quantity}
                            </strong>
                          </span>
                        </div>
                        <p className="mt-2 text-xs text-slate-500">
                          Unit price ·{" "}
                          <span className="text-slate-300">
                            ₦{parseFloat(item.price).toLocaleString()}
                          </span>
                        </p>
                      </div>

                      {/* Subtotal */}
                      <div className="flex flex-col items-end justify-center flex-shrink-0">
                        <p className="text-white font-semibold text-sm">
                          ₦{item.item_subtotal.toLocaleString()}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Order Timeline */}
              {statusKey !== "cancelled" && (
                <div className="fade-up fade-up-3 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 p-6">
                  <h2 className="text-base font-semibold text-white mb-6">
                    Order Progress
                  </h2>

                  <div className="relative">
                    {/* Background line */}
                    <div className="absolute left-4 top-4 bottom-4 w-px bg-slate-800" />

                    <ol className="space-y-6">
                      {TIMELINE_STEPS.map((step, idx) => {
                        const stepNum = idx + 1;
                        const isDone = currentStep >= stepNum;
                        const isActive = currentStep === stepNum;

                        return (
                          <li
                            key={step.key}
                            className="relative flex items-start gap-4 pl-0"
                          >
                            {/* Node */}
                            <div
                              className={`relative z-10 flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 transition-all duration-500 ${
                                isDone
                                  ? "border-emerald-500 bg-emerald-500/20 text-emerald-400"
                                  : isActive
                                    ? "border-sky-500 bg-sky-500/20 text-sky-400"
                                    : "border-slate-700 bg-slate-900 text-slate-600"
                              }`}
                            >
                              {isDone && !isActive ? (
                                <svg
                                  viewBox="0 0 20 20"
                                  fill="currentColor"
                                  className="w-3.5 h-3.5"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                              ) : (
                                step.icon
                              )}
                              {isActive && (
                                <span className="absolute inset-0 rounded-full animate-ping bg-sky-400 opacity-20" />
                              )}
                            </div>

                            {/* Text */}
                            <div className="pt-0.5">
                              <p
                                className={`text-sm font-semibold ${isDone ? "text-white" : "text-slate-500"}`}
                              >
                                {step.label}
                              </p>
                              <p
                                className={`text-xs mt-0.5 ${isDone ? "text-slate-400" : "text-slate-600"}`}
                              >
                                {step.desc}
                              </p>
                            </div>
                          </li>
                        );
                      })}
                    </ol>
                  </div>
                </div>
              )}

              {/* Cancelled banner */}
              {statusKey === "cancelled" && (
                <div className="fade-up fade-up-3 rounded-2xl border border-rose-500/20 bg-rose-500/5 px-6 py-5 flex items-start gap-4">
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-rose-500/10 border border-rose-500/20 flex items-center justify-center">
                    <svg
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      className="w-5 h-5 text-rose-400"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-rose-300">
                      Order Cancelled
                    </p>
                    <p className="mt-1 text-xs text-rose-400/70">
                      This order has been cancelled. If you have questions,
                      please contact support.
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* RIGHT: Summary + Meta */}
            <div className="space-y-6">
              {/* Price summary */}
              <div className="fade-up fade-up-3 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 overflow-hidden">
                <div className="border-b border-slate-800 px-6 py-5">
                  <h2 className="text-base font-semibold text-white">
                    Price Summary
                  </h2>
                </div>
                <div className="p-6 space-y-3">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Subtotal</span>
                    <span className="text-white">
                      ₦{subtotal?.toLocaleString()}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Shipping</span>
                    <span
                      className={
                        shipping === 0
                          ? "text-emerald-400 text-xs font-medium"
                          : "text-white"
                      }
                    >
                      {shipping === 0
                        ? "Free"
                        : `₦${shipping.toLocaleString()}`}
                    </span>
                  </div>
                  <div className="pt-3 mt-1 border-t border-slate-800 flex justify-between">
                    <span className="text-white font-semibold">Total</span>
                    <span className="text-white font-bold text-lg">
                      ₦{parseFloat(total).toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              {/* Order meta */}
              <div className="fade-up fade-up-4 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 overflow-hidden">
                <div className="border-b border-slate-800 px-6 py-5">
                  <h2 className="text-base font-semibold text-white">
                    Order Info
                  </h2>
                </div>
                <div className="p-6 space-y-4">
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Order ID
                    </p>
                    <p className="text-white text-xs font-mono break-all">
                      {order.order_id}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Placed On
                    </p>
                    <p className="text-white text-sm">
                      {new Date(order.created_at).toLocaleDateString("en-US", {
                        weekday: "long",
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                      })}
                    </p>
                    <p className="text-slate-500 text-xs mt-0.5">
                      {new Date(order.created_at).toLocaleTimeString("en-US", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-widest text-slate-500 mb-1">
                      Account
                    </p>
                    <p className="text-white text-sm truncate">{order.user}</p>
                  </div>
                </div>
              </div>

              {/* Help */}
              <div className="fade-up fade-up-5 rounded-2xl border border-slate-800 bg-slate-900/70 backdrop-blur-xl shadow-2xl shadow-black/30 p-6">
                <p className="text-xs uppercase tracking-widest text-slate-500 mb-3">
                  Need Help?
                </p>
                <p className="text-xs text-slate-400 mb-4 leading-relaxed">
                  If you have any issues with this order, our support team is
                  here to help.
                </p>
                <button className="w-full rounded-xl border border-slate-700 px-5 py-3 text-sm font-medium text-slate-300 transition hover:border-slate-500 hover:bg-slate-800 hover:text-white">
                  <a href="/contact">Contact Support</a>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Body>
  );
};

export default OrderDetailPage;
