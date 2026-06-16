import { useNavigate } from "react-router-dom";

const ViewSaleButton = ({ id, fetchUserCart }) => {
    const navigate = useNavigate();

    const handleClick = (e) => {
        e.preventDefault(); // Prevent default behavior if necessary
        fetchUserCart(); // Perform the action
        navigate(`/sales/${id}`); // Navigate programmatically
    };

    return (
        <button
            onClick={handleClick}
            className="border-2 border-gray-100 py-1 px-3 w-30 text-white text-sm text-nowrap whitespace-nowrap"
        >
            View
        </button>
    );
};

export default ViewSaleButton;
