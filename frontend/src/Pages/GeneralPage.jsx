import ClothCard from "../Components/ClothCard";
import { motion, AnimatePresence } from "framer-motion";

const EmptyState = () => (
  <motion.div
    initial={{ opacity: 0, y: 24 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ duration: 0.5, ease: "easeOut" }}
    className="flex flex-col items-center justify-center py-24 px-6 text-center"
  >
    {/* Icon */}
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

    {/* Copy */}
    <h3 className="text-lg font-semibold text-white tracking-tight">
      No products available
    </h3>
    <p className="mt-2 max-w-xs text-sm text-slate-400 leading-relaxed">
      There's nothing here yet. New drops are added regularly — check back soon.
    </p>

    {/* Subtle divider + hint */}
    <div className="mt-8 flex items-center gap-3">
      <span className="h-px w-12 bg-slate-700" />
      <span className="text-xs text-slate-600 uppercase tracking-widest">
        Stay tuned
      </span>
      <span className="h-px w-12 bg-slate-700" />
    </div>
  </motion.div>
);

const GeneralPage = ({ products }) => {
  return (
    <div className="container mx-auto px-4 py-6">
      {/* Loading */}
      {products === null && (
        <div className="flex justify-center py-24">
          <span className="loading loading-ring loading-lg" />
        </div>
      )}

      {/* Empty state */}
      <AnimatePresence>
        {products?.length === 0 && <EmptyState />}
      </AnimatePresence>

      {/* Grid */}
      <div className="grid grid-cols-1 gap-6">
        {products?.length > 0 &&
          products.map((product) => (
            <motion.div
              key={product.product_id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 1 }}
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
    </div>
  );
};

export default GeneralPage;
