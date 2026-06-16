import { Link } from "react-router-dom";

const CancelPage = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-red-200">
            <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
                <div className="mb-6">
                    <div className="text-red-500 mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-red-100">
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                            strokeWidth={2}
                            stroke="currentColor"
                            className="w-8 h-8"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M6 18L18 6M6 6l12 12"
                            />
                        </svg>
                    </div>
                </div>
                <h1 className="text-2xl font-bold text-gray-800">Payment Canceled</h1>
                <p className="text-gray-600 mt-4">
                    It seems like you canceled the payment process. If you need assistance, feel free to contact us.
                </p>
                <Link to="/me/carts" className="mt-6">
                    <a
                        href="/cart"
                        className="btn btn-error w-full"
                    >
                        Return to Cart
                    </a>
                </Link>
            </div>
        </div>
    );
};

export default CancelPage;
