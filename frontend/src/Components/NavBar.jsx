import { IoPersonOutline } from "react-icons/io5";
import { SlBag } from "react-icons/sl";
import { Link, useLocation } from "react-router-dom";
import { useState } from "react";
import { useSelector } from "react-redux";
import { useRetrieveUserQuery } from "../redux/features/auth/authApiSlice";
import { useGetProductsQuery } from "../redux/features/product/productApiSlice";
import useAuth from "../hooks/use-auth";
import { useGetCartQuery } from "../redux/features/cart/cartApiSlice";

const NavBar = ({ search }) => {
  const [searchItem, setSearchItem] = useState("");
  const { isAuthenticated } = useSelector((state) => state.auth);

  const { handleLogout } = useAuth();

  // Skip user and cart fetches when logged out — prevents 401 console noise
  const { data: user } = useRetrieveUserQuery(undefined, {
    skip: !isAuthenticated,
  });
  const { data: userCart } = useGetCartQuery(undefined, {
    skip: !isAuthenticated,
  });

  const adminUser = user?.is_staff;

  const { data: products } = useGetProductsQuery();
  const [, setFilteredProducts] = useState(products);
  const location = useLocation();

  const handleSearch = (e) => {
    const value = e.target.value.toLowerCase();
    setSearchItem(value);
    if (products?.products) {
      setFilteredProducts(
        products.products.filter((product) =>
          product.title.toLowerCase().includes(value),
        ),
      );
    }
  };

  const cartSize =
    userCart?.items?.reduce((total, item) => total + item.quantity, 0) || 0;

  return (
    <div className="flex items-center justify-between sm:mx-4 lg:mx-8 mt-2">
      {/* LEFT SECTION */}
      <div className="flex items-center gap-6 lg:gap-10">
        {/* Logo */}
        <a href="/">
          <img
            src="/images/LOGO.png"
            alt="Brand logo"
            className="h-16 sm:h-20 w-auto rounded-lg"
          />
        </a>

        {/* Navigation Links */}
        <div className="flex items-center gap-4 sm:gap-6 lg:gap-8 text-sm sm:text-base lg:text-lg font-courier">
          <Link to="/">
            <span
              className={`hover:underline hover:underline-offset-2
                ${
                  location.pathname === "/" || location.pathname === "/home"
                    ? "text-white underline underline-offset-4"
                    : "text-white"
                }`}
            >
              Presale
            </span>
          </Link>

          <Link to="/collaboration">
            <span
              className={`hover:underline hover:underline-offset-2
                ${
                  location.pathname === "/collaboration"
                    ? "text-white underline underline-offset-4"
                    : "text-white"
                }`}
            >
              Archive
            </span>
          </Link>
        </div>

        {/* Optional Search */}
        {search && (
          <div className="form-control hidden md:block">
            <input
              type="text"
              placeholder="Search"
              className="input input-bordered bg-black w-32 lg:w-auto"
              value={searchItem}
              onChange={handleSearch}
            />
          </div>
        )}
      </div>

      {/* RIGHT SECTION */}
      <div className="flex items-center">
        {/* Cart — only for non-admin authenticated users */}
        {isAuthenticated && !adminUser && (
          <a
            href="/me/carts"
            tabIndex={0}
            role="button"
            className="btn btn-ghost btn-circle"
          >
            <div className="indicator">
              <span className="badge badge-sm indicator-item">{cartSize}</span>
              <SlBag className="w-5 h-5" />
            </div>
          </a>
        )}

        {/* Avatar Dropdown */}
        <div className="dropdown dropdown-end">
          <div tabIndex={0} role="button" className="btn btn-ghost btn-circle">
            <IoPersonOutline className="w-6 h-6" />
          </div>

          <ul
            tabIndex={0}
            className="menu dropdown-content mt-3 w-36 rounded-md border border-gray-700 bg-black shadow-lg z-[100]"
          >
            <li>
              <Link
                to="/myaccount"
                className="font-arvo text-white hover:bg-gray-800 rounded-md"
              >
                My Account
              </Link>
            </li>

            {isAuthenticated ? (
              <li>
                <button
                  onClick={handleLogout}
                  className="font-arvo text-left text-white hover:bg-gray-800 rounded-md"
                >
                  Logout
                </button>
              </li>
            ) : (
              <li>
                <Link
                  to="/login"
                  className="font-arvo text-white hover:bg-gray-800 rounded-md"
                >
                  Login
                </Link>
              </li>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default NavBar;
