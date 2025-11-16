import { render, screen } from "@testing-library/react";

import { AppShell } from "@/components/layout/AppShell";

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/dashboard"),
}));

describe("AppShell", () => {
  it("renders sidebar navigation items", () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.getAllByRole("link", { name: "Dashboard" })[0]).toBeVisible();
    expect(screen.getByText(/Amazon Wholesale Analytics/i)).toBeInTheDocument();
  });
});
