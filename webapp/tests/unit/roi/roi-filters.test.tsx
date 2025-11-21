import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { RoiFilters } from "@/components/features/roi/RoiFilters";
import type { RoiTableFilters } from "@/lib/tableState/roi";

const renderFilters = (filters: RoiTableFilters = {}) => {
  const onApply = jest.fn();
  const onReset = jest.fn();
  const user = userEvent.setup();

  const view = render(<RoiFilters filters={filters} onApply={onApply} onReset={onReset} />);

  return {
    ...view,
    user,
    onApply,
    onReset,
  };
};

describe("RoiFilters", () => {
  it("applies the updated filters", async () => {
    const { user, onApply } = renderFilters({ roiMin: 5, vendor: "51", search: "headphones" });

    await user.clear(screen.getByPlaceholderText("Find ASIN or title"));
    await user.type(screen.getByPlaceholderText("Find ASIN or title"), "camera");
    await user.clear(screen.getByPlaceholderText("Vendor"));
    await user.type(screen.getByPlaceholderText("Vendor"), "77");
    await user.clear(screen.getByPlaceholderText("Category"));
    await user.type(screen.getByPlaceholderText("Category"), "Outdoors");
    await user.clear(screen.getByLabelText("ROI ≥ (%)"));
    await user.type(screen.getByLabelText("ROI ≥ (%)"), "12");
    await user.click(screen.getByText(/Observe only/i));

    await user.click(screen.getByRole("button", { name: /Apply filters/i }));

    expect(onApply).toHaveBeenCalledWith({
      roiMin: 12,
      vendor: "77",
      category: "Outdoors",
      search: "camera",
      observeOnly: true,
    });
  });

  it("resets filters back to defaults", async () => {
    const initial = {
      roiMin: 10,
      vendor: "123",
      category: "Beauty",
      search: "face oil",
      observeOnly: true,
    };
    const { user, onReset } = renderFilters(initial);

    await user.clear(screen.getByPlaceholderText("Find ASIN or title"));
    await user.type(screen.getByPlaceholderText("Find ASIN or title"), "modified");

    await user.click(screen.getByRole("button", { name: /Reset/i }));

    expect(onReset).toHaveBeenCalled();
    await waitFor(() => {
      expect(screen.getByPlaceholderText("Find ASIN or title")).toHaveValue("");
      expect(screen.getByPlaceholderText("Vendor")).toHaveValue("");
      expect(screen.getByPlaceholderText("Category")).toHaveValue("");
      expect(screen.getByLabelText("ROI ≥ (%)")).toHaveValue(0);
      expect(screen.getByLabelText(/Observe only/i)).not.toBeChecked();
    });
  });
});
