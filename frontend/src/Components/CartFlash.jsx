import React from "react";

const CartFlash = ({ apiData }) => {
  return (
    <div className="flex items-center gap-4 rounded-2xl border border-zinc-800 bg-black px-4 py-3 text-white shadow-2xl shadow-black/40">
      {/* Product Image */}
      <div className="shrink-0 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
        <img
          src={
            apiData?.image ||
            "https://img.daisyui.com/images/profile/demo/yellingwoman@192.webp"
          }
          alt={apiData?.product_name}
          className="h-20 w-20 object-cover"
        />
      </div>

      {/* Product Info */}
      <div className="min-w-0 flex-1">
        <div className="flex items-start justify-between gap-3">
          <h3 className="truncate text-sm font-semibold tracking-tight text-white">
            {apiData?.product_name}
          </h3>

          <span className="rounded-full bg-zinc-800 px-2 py-1 text-[10px] font-medium uppercase tracking-wide text-zinc-300">
            Added
          </span>
        </div>

        <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-400">
          {apiData?.color && (
            <span>
              Color: <span className="text-zinc-200">{apiData.color}</span>
            </span>
          )}

          {apiData?.size && (
            <span>
              Size: <span className="text-zinc-200">{apiData.size}</span>
            </span>
          )}

          <span>
            Qty:{" "}
            <span className="font-medium text-zinc-200">
              {apiData?.quantity}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default CartFlash;
