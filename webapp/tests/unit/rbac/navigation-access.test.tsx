import { render, screen } from "@testing-library/react";
import type { Session } from "next-auth";

import { AppShell } from "@/components/layout/AppShell";

const mockUseSession = jest.fn();

jest.mock("next/navigation", () => ({
  usePathname: () => "/dashboard",
}));

jest.mock("next-auth/react", () => ({
  useSession: () => mockUseSession(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Tester",
    email: "tester@example.com",
    roles,
  },
  expires: "",
});

describe("AppShell navigation RBAC", () => {
  afterEach(() => {
    mockUseSession.mockReset();
  });

  it("hides inbox and decision links for viewer", () => {
    mockUseSession.mockReturnValue({
      data: buildSession(["viewer"]),
      status: "authenticated",
    });

    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.queryAllByRole("link", { name: "Ingest" })).toHaveLength(0);
    expect(screen.queryAllByRole("link", { name: "Settings" })).toHaveLength(0);
    expect(screen.queryAllByRole("link", { name: "Inbox" })).toHaveLength(0);
    expect(screen.queryAllByRole("link", { name: "Decision Engine" })).toHaveLength(0);
  });

  it("shows Inbox only for ops role", () => {
    mockUseSession.mockReturnValue({
      data: buildSession(["ops"]),
      status: "authenticated",
    });

    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.getAllByRole("link", { name: "Ingest" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: "Settings" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: "Inbox" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.queryAllByRole("link", { name: "Decision Engine" })).toHaveLength(0);
  });

  it("shows both Inbox and Decision Engine for admin", () => {
    mockUseSession.mockReturnValue({
      data: buildSession(["admin"]),
      status: "authenticated",
    });

    render(
      <AppShell>
        <div>content</div>
      </AppShell>
    );

    expect(screen.getAllByRole("link", { name: "Ingest" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: "Settings" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: "Inbox" }).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByRole("link", { name: "Decision Engine" }).length).toBeGreaterThanOrEqual(1);
  });
});
