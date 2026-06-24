import ClothCard from "../Components/ClothCard";
import { motion, AnimatePresence } from "framer-motion";
import { FiChevronLeft, FiChevronRight } from "react-icons/fi";

const EmptyState = () => (
  <motion.div
    initial={{ opacity: 0, y: 24 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, ease: "easeOut" }}
    className="flex flex-col items-center justify-center py-24 px-6 text-center"
  >
    <div className="mb-6 flex h-20 w-20 items-center justify-center rounded-full border border-slate-700 bg-slate-900/60">
      <svg
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-9 w-9 text-slate-500"
      >
        <path
          d="M22 10C22 10 18 14 12 14V38C12 46 22 54 32 58C42 54 52 46 52 38V14C46 14 42 10 42 10L36 14H28L22 10Z"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
        <path
          d="M24 32h16M32 24v16"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
    </div>
    <h3 className="text-lg font-semibold text-white tracking-tight">
      No products available
    </h3>
    <p className="mt-2 max-w-xs text-sm text-slate-400 leading-relaxed">
      There's nothing here yet. New drops are added regularly — check back soon.
    </p>
    <div className="mt-8 flex items-center gap-3">
      <span className="h-px w-12 bg-slate-700" />
      <span className="text-xs text-slate-600 uppercase tracking-widest">
        Stay tuned
      </span>
      <span className="h-px w-12 bg-slate-700" />
    </div>
  </motion.div>
);

const GeneralPage = ({ data, page, onPageChange, isFetching }) => {
  const products = data?.products ?? [];
  const totalPages = data?.total_pages ?? 1;
  const total = data?.total ?? 0;
  const hasNext = data?.has_next ?? false;
  const hasPrev = data?.has_prev ?? false;

  return (
    <div className="container mx-auto px-4 py-6">
      {/* Loading skeleton on first load */}
      {data === undefined && (
        <div className="flex justify-center py-24">
          <span className="loading loading-ring loading-lg" />
        </div>
      )}

      {/* Empty state */}
      <AnimatePresence>
        {data !== undefined && products.length === 0 && <EmptyState />}
      </AnimatePresence>

      {/* Product grid — slight opacity while fetching a new page */}
      <div
        className={`grid grid-cols-1 gap-6 transition-opacity duration-200 ${isFetching ? "opacity-50" : "opacity-100"}`}
      >
        {products.map((product) => (
          <motion.div
            key={product.product_id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <ClothCard
              id={product.product_id}
              clothName={product.title}
              imgSrc={product?.images?.[0]}
              daysLeft={product.days_left}
              deadLine={product.goal}
              artist={product.artist_name}
              expire={product.is_expired}
              soldOut={product.is_sold_out}
            />
          </motion.div>
        ))}
      </div>

      {/* Pagination controls — only shown when there is more than one page */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-10 px-1">
          {/* Page info */}
          <p className="text-zinc-500 text-xs">
            Page {page} of {totalPages} &mdash; {total} product
            {total !== 1 ? "s" : ""}
          </p>

          {/* Prev / Next buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={!hasPrev || isFetching}
              className="flex items-center gap-1 px-3 py-1.5 border border-zinc-700 text-zinc-400
                hover:border-white hover:text-white transition-colors text-xs
                disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Previous page"
            >
              <FiChevronLeft className="w-3.5 h-3.5" />
              Prev
            </button>

            {/* Page number pills */}
            <div className="hidden sm:flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
                <button
                  key={p}
                  onClick={() => onPageChange(p)}
                  disabled={isFetching}
                  className={`w-7 h-7 text-xs border transition-colors
                    ${
                      p === page
                        ? "border-white bg-white text-black"
                        : "border-zinc-700 text-zinc-400 hover:border-zinc-400 hover:text-white"
                    } disabled:opacity-30 disabled:cursor-not-allowed`}
                >
                  {p}
                </button>
              ))}
            </div>

            <button
              onClick={() => onPageChange(page + 1)}
              disabled={!hasNext || isFetching}
              className="flex items-center gap-1 px-3 py-1.5 border border-zinc-700 text-zinc-400
                hover:border-white hover:text-white transition-colors text-xs
                disabled:opacity-30 disabled:cursor-not-allowed"
              aria-label="Next page"
            >
              Next
              <FiChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default GeneralPage;
