import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button } from "@/components/ui";

describe("Button", () => {
  it("renders the provided label", () => {
    render(<Button>Save changes</Button>);
    expect(screen.getByRole("button", { name: "Save changes" })).toBeInTheDocument();
  });

  it("supports different sizes", () => {
    render(<Button size="lg">Large button</Button>);
    const button = screen.getByRole("button", { name: "Large button" });
    expect(button.className).toContain("h-11");
  });

  it("invokes onClick when enabled", async () => {
    const user = userEvent.setup();
    const handleClick = jest.fn();
    render(
      <Button onClick={handleClick} variant="outline">
        Click me
      </Button>
    );
    await user.click(screen.getByRole("button", { name: "Click me" }));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it("disables the button while loading", () => {
    render(
      <Button isLoading size="sm">
        Submit
      </Button>
    );
    const button = screen.getByRole("button", { name: /Submit/i });
    expect(button).toBeDisabled();
    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });
});
