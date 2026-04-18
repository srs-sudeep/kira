import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders without crashing", () => {
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    // App renders an Outlet (empty by default) inside an ErrorBoundary.
    // Just verifying that mount succeeds without throwing.
    expect(document.body).toBeTruthy();
  });
});
