import { Navigate, Route, Routes } from "react-router-dom";
import { Toaster } from "sonner";
import { Provider } from "react-redux";
import store from "./redux/store";

import PublicRoute from "./Components/PublicRoute";
import PrivateRoute from "./Components/PrivateRoute";
import ChatWidget from "./Components/ChatWidget";

import Sale from "./Components/Sale";
import LoginPage from "./Pages/LoginPage";
import LandingPage from "./Pages/LandingPage";
import NewUser from "./Pages/RegistrationPage";
import HomePage from "./Pages/HomePage";
import CartPage from "./Pages/CartPage";
import SuccessPage from "./Pages/SuccessPage";
import CancelPage from "./Pages/CancelPage";
import ResetRequestPage from "./Pages/ResetRequestPage";
import ResetPage from "./Pages/ResetPage";
import ArchivePage from "./Pages/ArchivePage";
import ContactPage from "./Components/Contact";
import AccountPage from "./Pages/AccountPage";
import EditUserPage from "./Pages/EditUserPage";
import OrderDetailPage from "./Pages/OrderDetailPage";

function App() {
  return (
    <Provider store={store}>
      <div
        className="min-h-screen flex flex-col bg-opacity-85 text-white overflow-hidden"
        style={{ backgroundColor: "#000" }}
      >
        <Toaster
          position="top-right"
          expand={true}
          richColors
          toastOptions={{
            classNames: {
              toast: "bg-black border border-zinc-800 text-white shadow-2xl",
              title: "text-white",
              description: "text-zinc-400",
              actionButton: "bg-white text-black hover:bg-zinc-200",
              cancelButton: "bg-zinc-800 text-white hover:bg-zinc-700",
            },
          }}
        />

        <Routes>
          {/* Public routes */}
          <Route
            path="/"
            element={
              <PublicRoute>
                <LandingPage />
              </PublicRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <NewUser />
              </PublicRoute>
            }
          />
          <Route
            path="/reset-request"
            element={
              <PublicRoute>
                <ResetRequestPage />
              </PublicRoute>
            }
          />
          <Route
            path="/password-reset/:uid/:token"
            element={
              <PublicRoute>
                <ResetPage />
              </PublicRoute>
            }
          />

          {/* Private routes */}
          <Route
            path="/home"
            element={
              <PrivateRoute>
                <HomePage />
              </PrivateRoute>
            }
          />
          <Route
            path="/myaccount"
            element={
              <PrivateRoute>
                <AccountPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/editUser"
            element={
              <PrivateRoute>
                <EditUserPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/me/carts"
            element={
              <PrivateRoute>
                <CartPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/order/success"
            element={
              <PrivateRoute>
                <SuccessPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/order/cancel"
            element={
              <PrivateRoute>
                <CancelPage />
              </PrivateRoute>
            }
          />
          <Route
            path="/orders/:orderId"
            element={
              <PrivateRoute>
                <OrderDetailPage />
              </PrivateRoute>
            }
          />

          {/* Open routes */}
          <Route path="/sales/:id" element={<Sale />} />
          <Route path="/collaboration" element={<ArchivePage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="*" element={<Navigate to="/home" />} />
        </Routes>

        {/* ChatWidget renders on all pages — floats bottom-right */}
        <ChatWidget />
      </div>
    </Provider>
  );
}

export default App;
