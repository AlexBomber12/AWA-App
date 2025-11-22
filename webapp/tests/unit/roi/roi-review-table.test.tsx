import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RoiReviewTable } from "@/components/features/roi/RoiReviewTable";

beforeAll(() => {
  if (!Element.prototype.hasPointerCapture) {
    Element.prototype.hasPointerCapture = () => false;
  }
  if (!Element.prototype.releasePointerCapture) {
    Element.prototype.releasePointerCapture = () => {};
  }
  if (!Element.prototype.scrollIntoView) {
    Element.prototype.scrollIntoView = () => {};
  }
});

describe("RoiReviewTable", () => {
  it("filters by owner and can reset to defaults", async () => {
    const user = userEvent.setup();
    render(<RoiReviewTable />);

    const ownerInput = screen.getByPlaceholderText(/Search owner/i);

    expect(screen.getAllByRole("row")).toHaveLength(5);

    await user.type(ownerInput, "L2");
    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    const filteredRows = screen.getAllByRole("row");
    expect(filteredRows).toHaveLength(2);
    expect(screen.getByText("AMZ-RED-425")).toBeInTheDocument();

    await user.clear(ownerInput);
    await user.click(screen.getByRole("button", { name: /Reset/i }));

    expect(await screen.findAllByRole("row")).toHaveLength(5);
  });

  it("filters by status", async () => {
    const user = userEvent.setup();
    render(<RoiReviewTable />);

    const statusTrigger = screen.getAllByRole("combobox")[0];

    await user.click(statusTrigger);
    const rejectedOption = await screen.findByRole("option", { name: /Rejected/i });
    await user.click(rejectedOption);
    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    const rows = screen.getAllByRole("row");
    expect(rows).toHaveLength(2);
    expect(screen.getByText("AMZ-RED-510")).toBeInTheDocument();
  });
});
