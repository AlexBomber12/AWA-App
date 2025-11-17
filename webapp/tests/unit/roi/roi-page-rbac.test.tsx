import { render, screen } from "@testing-library/react";
import React from "react";

import { RoiPage } from "@/components/features/roi/RoiPage";
import { usePermissions } from "@/lib/permissions";

jest.mock("@/components/features/roi/RoiTableContainer", () => ({
  RoiTableContainer: ({ canApprove, onActionsChange }: { canApprove: boolean; onActionsChange?: (node: React.ReactNode | null) => void }) => {
    React.useEffect(() => {
      onActionsChange?.(<button>Approve pending rows</button>);
    }, [onActionsChange]);
    return <div data-testid="roi-table">{canApprove ? "can-approve" : "view-only"}</div>;
  },
}));

jest.mock("@/lib/permissions", () => ({
  usePermissions: jest.fn(),
}));

const mockedPermissions = usePermissions as unknown as jest.MockedFunction<typeof usePermissions>;

describe("RoiPage RBAC handling", () => {
  beforeEach(() => {
    mockedPermissions.mockReturnValue({
      roles: [],
      can: () => false,
      hasRole: () => false,
    });
  });

  it("hides bulk approve actions for users without permission", () => {
    render(<RoiPage />);

    expect(screen.queryByText(/Approve pending rows/i)).not.toBeInTheDocument();
    expect(screen.getByTestId("roi-table")).toHaveTextContent("view-only");
  });

  it("exposes bulk approve actions when permission is granted", () => {
    mockedPermissions.mockReturnValue({
      roles: ["ops"],
      can: ({ action }) => action === "approve",
      hasRole: () => true,
    });

    render(<RoiPage />);

    expect(screen.getByText(/Approve pending rows/i)).toBeInTheDocument();
    expect(screen.getByTestId("roi-table")).toHaveTextContent("can-approve");
  });
});
