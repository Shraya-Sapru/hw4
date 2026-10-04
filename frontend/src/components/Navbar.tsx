import { NavLink, useNavigate } from "react-router-dom";
import { logout } from "../lib/auth";
import { useAuth } from "../lib/useAuth";
import "./Navbar.css";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? "nav-link nav-link--active" : "nav-link";

export default function Navbar() {
  const { user } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <header className="navbar">
      <div className="navbar__inner">
        <NavLink to="/" className="navbar__brand">
          Campus Customs
        </NavLink>
        <nav className="navbar__links">
          <NavLink to="/" end className={navLinkClass}>
            Home
          </NavLink>
          <NavLink to="/products" className={navLinkClass}>
            Products
          </NavLink>
          <NavLink to="/about" className={navLinkClass}>
            About Us
          </NavLink>

          {user ? (
            <>
              <span className="nav-link nav-link--greeting">Hi, {user.first_name}</span>
              <button type="button" className="nav-link nav-link--cta" onClick={handleLogout}>
                Log out
              </button>
            </>
          ) : (
            <>
              <NavLink to="/login" className={navLinkClass}>
                Log in
              </NavLink>
              <NavLink to="/signup" className="nav-link nav-link--cta">
                Create account
              </NavLink>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
