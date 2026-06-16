import { Link, useNavigate } from "react-router-dom";
import ProgressBar from "./ProgressBar";

const ClothCard = ({
  id,
  imgSrc,
  clothName,
  deadLine,
  daysLeft,
  artist,
  expire,
  soldOut,
}) => {
  const navigate = useNavigate();

  return (
    // Return clothcard as anchor tag
    <div
      onClick={() => navigate(`/sales/${id}`)}
      className="bg-inherit border-2 border-white p-4 font-courier flex flex-col sm:flex-row gap-8 cursor-pointer"
    >
      {/* Image */}
      <div className="w-full sm:w-[20%] flex flex-shrink-0 justify-center items-center">
        <img
          className="w-full h-auto max-h-52 object-cover"
          src={imgSrc}
          alt={clothName.slice(0, 5)}
        />
      </div>

      {/* Details */}
      <div className="w-full sm:w-[80%] flex flex-col flex-grow gap-4 justify-center">
        {/* Name and button */}
        <div className="flex justify-between items-center gap-8">
          <p className="text-white text-xl sm:text-2xl">
            {clothName} X {artist}
          </p>
          <Link
            to={`/sales/${id}`}
            className="hidden sm:block border-2 border-gray-100 py-1 px-3 text-white text-xl hover:text-red-500 whitespace-nowrap"
          >
            View
          </Link>
        </div>

        {/* Preorder stand alone on extra small screen */}
        {daysLeft > 0 && !expire && !soldOut && (
          <p className="sm:hidden self-center text-lg">
            Pre-order only {deadLine} days
          </p>
        )}
        {/* Progress bar */}
        <div>
          {daysLeft > 0 && !expire && !soldOut ? (
            <div>
              <p className="flex justify-end sm:justify-between text-white text-lg gap-8 sm:pt-12">
                <span className="hidden sm:block">
                  - Pre-order only {deadLine} days
                </span>
                <span>- {daysLeft} Days Left</span>
              </p>
              <ProgressBar daysLeft={daysLeft} deadLine={deadLine} />
            </div>
          ) : (
            <p className="self-start text-red-600">- Sale end</p>
          )}
        </div>
        {/* Standalone sales button */}
        <Link
          to={`/sales/${id}`}
          className="sm:hidden border-2 border-gray-100 py-1 px-3 text-white text-xl text-center hover:bg-gray-500 whitespace-nowrap"
        >
          View
        </Link>
      </div>
    </div>
  );
};

export default ClothCard;
