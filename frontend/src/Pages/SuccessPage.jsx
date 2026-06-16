const SuccessPage = () => {
    return (
        <div className="min-h-screen flex items-center justify-center bg-green-100 px-4">
            <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
                <div className="mb-6">
                    <div className="text-green-500 mx-auto w-16 h-16 flex items-center justify-center rounded-full bg-green-100">
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
                                d="M5 13l4 4L19 7"
                            />
                        </svg>
                    </div>
                </div>
                <h1 className="text-2xl font-bold text-gray-800">Payment Successful!</h1>
                <p className="text-gray-600 mt-4">
                    Thank you for your purchase. Your payment was processed successfully!
                </p>
                <div className="mt-6">
                    <a
                        href="/home"
                        className="btn btn-primary w-full"
                    >
                        Back to Home
                    </a>
                </div>
            </div>
        </div>
    );
};

export default SuccessPage