import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import ChatWidget from "./components/ChatWidget";
import Home from "./pages/Home";
import Products from "./pages/Products";
import ProductDetail from "./pages/ProductDetail";
import AboutUs from "./pages/AboutUs";
import Login from "./pages/Login";
import CreateAccount from "./pages/CreateAccount";
import "./App.css";

export default function App() {
  return (
    <>
      <Navbar />
      <main className="app-main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<CreateAccount />} />
        </Routes>
      </main>
      <ChatWidget />
    </>
  );
}
