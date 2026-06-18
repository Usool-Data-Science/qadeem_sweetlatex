import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { MdClose, MdFileUpload, MdSearch } from "react-icons/md";
import { useVisualSearchMutation } from "../redux/features/recommendations/recommendationsApiSlice";

const VisualSearchModal = ({ isOpen, onClose }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState(null);
  const [base64Image, setBase64Image] = useState(null);
  const [results, setResults] = useState([]);
  const [searched, setSearched] = useState(false);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const [visualSearch, { isLoading }] = useVisualSearchMutation();

  const readFile = (file) => {
    if (!file || !file.type.startsWith("image/")) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const dataUrl = e.target.result;
      setPreview(dataUrl);
      // Strip the data:image/...;base64, prefix — API wants raw base64
      setBase64Image(dataUrl.split(",")[1]);
      setResults([]);
      setSearched(false);
    };
    reader.readAsDataURL(file);
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    readFile(file);
  }, []);

  const onDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const onDragLeave = () => setIsDragging(false);

  const handleFileInput = (e) => readFile(e.target.files[0]);

  const handleSearch = async () => {
    if (!base64Image) return;
    try {
      const result = await visualSearch({
        image_base64: base64Image,
        top_k: 12,
      }).unwrap();
      setResults(result.results || []);
      setSearched(true);
    } catch {
      setResults([]);
      setSearched(true);
    }
  };

  const handleReset = () => {
    setPreview(null);
    setBase64Image(null);
    setResults([]);
    setSearched(false);
  };

  const handleClose = () => {
    handleReset();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-80"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative z-10 bg-black border border-zinc-700 w-full max-w-2xl mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-zinc-800">
          <h2 className="text-white text-lg font-medium">Visual Search</h2>
          <button
            onClick={handleClose}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <MdClose className="w-6 h-6" />
          </button>
        </div>

        <div className="p-4 space-y-4">
          {/* Drop zone */}
          {!preview ? (
            <div
              onDrop={onDrop}
              onDragOver={onDragOver}
              onDragLeave={onDragLeave}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-none p-12 text-center cursor-pointer transition-colors ${
                isDragging
                  ? "border-white bg-zinc-900"
                  : "border-zinc-600 hover:border-zinc-400"
              }`}
            >
              <MdFileUpload className="w-12 h-12 text-zinc-500 mx-auto mb-3" />
              <p className="text-white text-sm">
                Drop an image here or click to upload
              </p>
              <p className="text-zinc-500 text-xs mt-1">
                PNG, JPG, WEBP — find visually similar products
              </p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileInput}
              />
            </div>
          ) : (
            /* Preview + search */
            <div className="space-y-4">
              <div className="flex gap-4 items-start">
                <img
                  src={preview}
                  alt="Search preview"
                  className="w-32 h-32 object-cover border border-zinc-700"
                />
                <div className="flex flex-col gap-2">
                  <button
                    onClick={handleSearch}
                    disabled={isLoading}
                    className="flex items-center gap-2 border border-white text-white px-4 py-2 hover:bg-white hover:text-black transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    <MdSearch className="w-4 h-4" />
                    {isLoading ? "Searching..." : "Find Similar Items"}
                  </button>
                  <button
                    onClick={handleReset}
                    className="text-zinc-500 hover:text-white text-sm transition-colors"
                  >
                    Use a different image
                  </button>
                </div>
              </div>

              {/* Results */}
              {searched && (
                <div>
                  {results.length === 0 ? (
                    <p className="text-zinc-400 text-sm text-center py-6">
                      No similar items found. Try a different image.
                    </p>
                  ) : (
                    <>
                      <p className="text-zinc-400 text-xs mb-3">
                        {results.length} similar items found
                      </p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                        {results.map((product) => (
                          <div
                            key={product.product_id}
                            onClick={() => {
                              navigate(`/sales/${product.product_id}`);
                              handleClose();
                            }}
                            className="cursor-pointer group border border-zinc-800 hover:border-white transition-colors"
                          >
                            <div className="w-full h-32 bg-zinc-900 overflow-hidden">
                              {product.image_url ? (
                                <img
                                  src={product.image_url}
                                  alt={product.title}
                                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                                />
                              ) : (
                                <div className="w-full h-full flex items-center justify-center text-zinc-600 text-xs">
                                  No image
                                </div>
                              )}
                            </div>
                            <div className="p-2 bg-black">
                              <p className="text-white text-xs truncate">
                                {product.title}
                              </p>
                              <p className="text-zinc-400 text-xs">
                                £{product.price}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default VisualSearchModal;
