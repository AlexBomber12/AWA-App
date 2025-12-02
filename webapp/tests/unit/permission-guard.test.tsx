import { render, screen } from "@testing-library/react";
import type { Session } from "next-auth";
import { useSession } from "next-auth/react";

import { PermissionGuard } from "@/lib/permissions/client";

jest.mock("next-auth/react", () => ({
  useSession: jest.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
jest.mock("next/navigation", () => ({
  useRouter: () => ({ replace: jest.fn() }),
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

  it("blocks when required roles are missing", () => {
    render(
      <PermissionGuard requiredRoles={["admin"]} fallback={<p>Role blocked</p>}>
        <span>Hidden</span>
      </PermissionGuard>
    );

    expect(screen.getByText("Role blocked")).toBeInTheDocument();
  });

  it("renders nothing when access is denied and no fallback is provided", () => {
    mockUseSession.mockReturnValueOnce({
      data: buildSession(["viewer"]),
      status: "authenticated",
    });

    const { container } = render(
      <PermissionGuard resource="inbox" action="view">
        <span>Hidden</span>
      </PermissionGuard>
    );

    expect(container).toBeEmptyDOMElement();
  });
});
