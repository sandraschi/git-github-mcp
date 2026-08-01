import React from "react";
import ReactDOM from "react-dom/client";
import { LoggerProvider } from "@/context/logger-context";
import App from "./App.tsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <LoggerProvider>
      <App />
    </LoggerProvider>
  </React.StrictMode>,
);
