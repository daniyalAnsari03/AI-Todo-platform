import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import DashboardSidebar from "../DashboardSidebar";
import LandingNavigation from "../LandingNavigation";

describe("responsive navigation", () => {
  it("opens and closes the dashboard menu with Escape and restores focus", async () => {
    const user = userEvent.setup();
    render(<DashboardSidebar userName="Alice" />);

    const menuButton = screen.getByRole("button", { name: "Open dashboard menu" });
    await user.click(menuButton);

    expect(menuButton).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByRole("dialog", { name: "Dashboard menu" })).toBeInTheDocument();
    expect(within(screen.getByRole("dialog", { name: "Dashboard menu" })).getByText("Alice")).toBeInTheDocument();

    await user.keyboard("{Escape}");

    expect(menuButton).toHaveAttribute("aria-expanded", "false");
    expect(menuButton).toHaveFocus();
  });

  it("opens the landing navigation from its mobile menu button", async () => {
    const user = userEvent.setup();
    render(<LandingNavigation isAuthenticated={false} />);

    const menuButton = screen.getByRole("button", { name: "Open main menu" });
    await user.click(menuButton);

    expect(menuButton).toHaveAttribute("aria-expanded", "true");
    const mobileNavigation = screen.getByRole("navigation", {
      name: "Mobile main navigation",
    });
    expect(within(mobileNavigation).getByRole("link", { name: "Features" })).toHaveAttribute(
      "href",
      "#features",
    );
    expect(within(mobileNavigation).getByRole("link", { name: "Get Started" })).toHaveClass(
      "nav-cta",
    );
  });
});
