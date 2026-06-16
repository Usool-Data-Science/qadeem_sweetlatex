import NavBar from "./NavBar";

const Body = ({ loginButton, children }) => {
  return (
    <div className="flex flex-col min-h-screen font-courier">
      {/* Navbar */}
      <NavBar loginButton={loginButton} />
      <div className="flex-grow mx-4 px-2 py-2">{children}</div>

      {/* Footer: It stays at the bottom when content is short */}
      <footer className="py-6 flex flex-col sm:flex-row flex-wrap px-10 sm:justify-between gap-4">
        <div className="flex gap-4 justify-between font-courier text-lg">
          <a href="https://www.instagram.com/sweet.latex" target="_blank">
            <span className="text-white hover:underline hover:underline-offset-2">
              Instagram
            </span>
          </a>
          <a href="/contact">Contact</a>
        </div>
        <p className="text-sm sm:text-lg" style={{ fontSize: "12px" }}>
          © 2025 Sweet Latex. All Rights Reserved
        </p>
      </footer>
    </div>
  );
};

export default Body;
