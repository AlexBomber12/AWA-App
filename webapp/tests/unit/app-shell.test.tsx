import { render, screen } from "@testing-library/react";

import { AppShell } from "@/components/layout/AppShell";

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(() => "/dashboard"),
}));

jest.mock("next-auth/react", () => ({
  useSession: jest.fn(() => ({
    data: {
      user: { roles: ["admin"] },
    },
    status: "authenticated",
  })),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe("AppShell", () => {
  it("renders sidebar navigation items for authorized user", () => {
    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.getAllByRole("link", { name: "Dashboard" })[0]).toBeVisible();
    expect(screen.getAllByRole("link", { name: "Inbox" })[0]).toBeVisible();
    expect(screen.getByText(/Amazon Wholesale Analytics/i)).toBeInTheDocument();
  });
});
