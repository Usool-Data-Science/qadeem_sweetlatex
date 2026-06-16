import { motion } from "framer-motion";
import { useState } from "react";

const Carousel = ({ subImages }) => {
  const [selectedImage, setSelectedImage] = useState(subImages[0]);
  const [startIndex, setStartIndex] = useState(0);
  const visibleImages = 3;

  const handleNext = () => {
    setStartIndex((prevIndex) => (prevIndex + 1) % subImages.length);
  };

  const handlePrevious = () => {
    setStartIndex(
      (prevIndex) => (prevIndex - 1 + subImages.length) % subImages.length,
    );
  };

  return (
    <motion.div className="flex flex-col sm:flex-row sm:w-full items-center gap-4">
      {/* Main image for smaller screens */}
      <div className="w-full sm:hidden">
        <img
          className="h-auto w-full object-cover"
          src={selectedImage}
          alt="Main"
        />
      </div>

      {/* Thumbnails for smaller screens */}
      <div
        className="sm:hidden flex items-center gap-1 w-full"
        style={{ height: "80px" }}
      >
        <button className="w-[5%]" onClick={handlePrevious}>
          <img
            src="/images/arrowLeft.jpg"
            className="h-auto w-full bg-transparent"
          />
        </button>

        <motion.div
          className="h-full w-[90%] flex justify-center overflow-hidden cursor-grab active:cursor-grabbing"
          drag="x"
          dragConstraints={{ left: 0, right: 0 }}
          whileTap={{ cursor: "grabbing" }}
          dragTransition={{ bounceStiffness: 300, bounceDamping: 20 }}
          onDragEnd={(event, info) => {
            if (info.offset.x < -50) handleNext(); // swipe left
            if (info.offset.x > 50) handlePrevious(); // swipe right
          }}
        >
          {[...Array(visibleImages)].map((_, index) => {
            const imgIndex = (startIndex + index) % subImages.length;

            return (
              <img
                key={index}
                src={subImages[imgIndex]}
                alt={`Slide ${imgIndex}`}
                className="w-[33%] h-auto object-cover mx-1 cursor-pointer"
                onClick={() => setSelectedImage(subImages[imgIndex])}
              />
            );
          })}
        </motion.div>

        <button className="w-[5%]" onClick={handleNext}>
          <img
            src="/images/arrowRight.jpg"
            className="h-auto w-full bg-transparent"
          />
        </button>
      </div>

      {/* Thumbnails for larger screens */}
      <div
        className="hidden sm:flex sm:flex-col sm:w-[20%] sm:items-center"
        style={{ height: "578px" }}
      >
        <button
          style={{ height: "19px", width: "38px" }}
          onClick={handlePrevious}
        >
          <img
            src="/images/arrowUp.jpg"
            style={{ height: "19px", width: "38px" }}
          />
        </button>

        <motion.div
          className="h-[95%] mt-2 flex sm:flex-col justify-center overflow-hidden sm:gap-2 w-full cursor-grab active:cursor-grabbing"
          drag="y"
          dragConstraints={{ top: 0, bottom: 0 }}
          whileTap={{ cursor: "grabbing" }}
          dragTransition={{ bounceStiffness: 300, bounceDamping: 20 }}
          onDragEnd={(event, info) => {
            if (info.offset.y < -50) handleNext(); // swipe up
            if (info.offset.y > 50) handlePrevious(); // swipe down
          }}
        >
          {[...Array(visibleImages)].map((_, index) => {
            const imgIndex = (startIndex + index) % subImages.length;

            return (
              <img
                key={index}
                src={subImages[imgIndex]}
                alt={`Slide ${imgIndex}`}
                className="h-[33%] w-full object-cover cursor-pointer"
                onClick={() => setSelectedImage(subImages[imgIndex])}
              />
            );
          })}
        </motion.div>

        <button
          className="pt-2"
          style={{ height: "19px", width: "38px" }}
          onClick={handleNext}
        >
          <img
            src="/images/arrowDown.jpg"
            style={{ height: "19px", width: "38px" }}
          />
        </button>
      </div>

      {/* Main image for larger screens */}
      <div className="hidden sm:w-[80%] sm:block">
        <img
          className="h-auto w-full pt-2 object-cover"
          style={{ height: "540px" }}
          src={selectedImage}
          alt="Main image"
        />
      </div>
    </motion.div>
  );
};

export default Carousel;
