import React from "react";
import ReactDOM from "react-dom/client";
import { LoggerProvider } from "@/context/logger-context";
import App from "./App.tsx";
import "./index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found");
}
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <LoggerProvider>
      <App />
    </LoggerProvider>
  </React.StrictMode>,
);
