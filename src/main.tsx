import React from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import App from "./App";
import "./App.css";
import ModeWrapper from "./components/ModeWrapper";
import { ThemeProvider } from "./components/theme-provider";
import Detail from "./routes/Detail";
import Rack from "./routes/Rack";
import Test from "./routes/test";

const router = createBrowserRouter(
  [
    {
      path: "/",
      element: <App />,
    },
    {
      path: "/details/:id",
      element: <Detail />,
    },
    {
      path: "/rack/:id",
      element: <Rack />,
    },

    {
      path: "/test",
      element: <Test />,
    },
  ],
  {
    future: {
      v7_relativeSplatPath: true,
    },
  },
);
ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ThemeProvider defaultTheme="dark" storageKey="vite-ui-theme">
      <ModeWrapper>
        <RouterProvider router={router} future={{ v7_startTransition: true }} />
      </ModeWrapper>
    </ThemeProvider>
  </React.StrictMode>,
);
