import { render, screen } from "@testing-library/react";
import type { Session } from "next-auth";
import { useSession } from "next-auth/react";

import { PermissionGuard } from "@/lib/permissions";

jest.mock("next-auth/react", () => ({
  useSession: jest.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>;

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Test User",
    email: "test@example.com",
    roles,
  },
  expires: "",
});

describe("PermissionGuard", () => {
  beforeEach(() => {
    mockUseSession.mockReturnValue({
      data: buildSession(["viewer"]),
      status: "authenticated",
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("renders children when access is granted", () => {
    render(
      <PermissionGuard resource="dashboard" action="view">
        <span>Allowed content</span>
      </PermissionGuard>
    );

    expect(screen.getByText("Allowed content")).toBeInTheDocument();
  });

  it("renders the fallback when access is denied", () => {
    mockUseSession.mockReturnValueOnce({
      data: buildSession(["viewer"]),
      status: "authenticated",
    });

    render(
      <PermissionGuard resource="inbox" action="view" fallback={<p>No access</p>}>
        <span>Hidden</span>
      </PermissionGuard>
    );

    expect(screen.getByText("No access")).toBeInTheDocument();
  });
});
