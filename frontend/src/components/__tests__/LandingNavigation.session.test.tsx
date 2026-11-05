import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import LandingNavigation from "../LandingNavigation";

describe("session-aware landing navigation", () => {
  it("B1: desktop navigation switches between public and authenticated links", () => {
    const { rerender } = render(<LandingNavigation isAuthenticated={false} />);

    let desktop = within(screen.getByRole("navigation", { name: "Main navigation" }));
    expect(desktop.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(desktop.getByRole("link", { name: "Features" })).toHaveAttribute("href", "#features");
    expect(desktop.getByRole("link", { name: "About" })).toHaveAttribute("href", "#about");
    expect(desktop.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(desktop.getByRole("link", { name: "Get Started" })).toHaveAttribute(
      "href",
      "/register",
    );

    rerender(<LandingNavigation isAuthenticated />);

    desktop = within(screen.getByRole("navigation", { name: "Main navigation" }));
    expect(desktop.getByRole("link", { name: "Home" })).toHaveAttribute("href", "/");
    expect(desktop.getByRole("link", { name: "Features" })).toHaveAttribute("href", "#features");
    expect(desktop.getByRole("link", { name: "About" })).toHaveAttribute("href", "#about");
    expect(desktop.getByRole("link", { name: "Dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(desktop.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    expect(desktop.queryByRole("link", { name: "Get Started" })).not.toBeInTheDocument();
  });

  it("B2: mobile navigation switches the same way inside the opened menu", async () => {
    const user = userEvent.setup();
    const { rerender } = render(<LandingNavigation isAuthenticated={false} />);

    await user.click(screen.getByRole("button", { name: "Open main menu" }));

    let mobile = within(
      screen.getByRole("navigation", { name: "Mobile main navigation" }),
    );
    expect(mobile.getByRole("link", { name: "Login" })).toHaveAttribute("href", "/login");
    expect(mobile.getByRole("link", { name: "Get Started" })).toHaveAttribute(
      "href",
      "/register",
    );

    rerender(<LandingNavigation isAuthenticated />);

    mobile = within(screen.getByRole("navigation", { name: "Mobile main navigation" }));
    expect(mobile.getByRole("link", { name: "Dashboard" })).toHaveAttribute(
      "href",
      "/dashboard",
    );
    expect(mobile.queryByRole("link", { name: "Login" })).not.toBeInTheDocument();
    expect(mobile.queryByRole("link", { name: "Get Started" })).not.toBeInTheDocument();
  });
});
