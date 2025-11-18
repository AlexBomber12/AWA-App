import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { z } from "zod";

import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/forms/Form";

const schema = z.object({
  name: z.string().min(3, "Name must be at least 3 characters."),
});

const renderTestForm = (
  props: Partial<React.ComponentProps<typeof Form<typeof schema>>> = {},
  onSubmit = jest.fn()
) => {
  return render(
    <Form
      schema={schema}
      defaultValues={{ name: "" }}
      onSubmit={onSubmit}
      apiError={props.apiError ?? null}
    >
      {(form) => (
        <>
          <FormField
            control={form.control}
            name="name"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Name</FormLabel>
                <FormControl>
                  <input data-testid="name-input" placeholder="Name" {...field} />
                </FormControl>
                <FormDescription>Enter at least 3 characters.</FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
          <button type="submit">Save</button>
        </>
      )}
    </Form>
  );
};

describe("Form primitives", () => {
  const user = userEvent.setup();

  it("submits valid values", async () => {
    const handleSubmit = jest.fn();
    renderTestForm({}, handleSubmit);

    await user.type(screen.getByTestId("name-input"), "Alpine");
    await user.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => expect(handleSubmit).toHaveBeenCalledWith({ name: "Alpine" }));
    expect(screen.queryByText(/must be at least 3/i)).not.toBeInTheDocument();
  });

  it("shows validation errors without invoking submit handler", async () => {
    const handleSubmit = jest.fn();
    renderTestForm({}, handleSubmit);

    await user.type(screen.getByTestId("name-input"), "ab");
    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(await screen.findByText(/name must be at least 3 characters/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it("hydrates API field errors into the form", async () => {
    const handleSubmit = jest.fn();
    const { rerender } = renderTestForm({}, handleSubmit);

    const apiError = {
      code: "VALIDATION_ERROR",
      message: "Please fix the highlighted fields.",
      status: 400,
      details: {
        fieldErrors: {
          name: "Server-side validation failed.",
        },
      },
    };

    rerender(
      <Form schema={schema} defaultValues={{ name: "" }} onSubmit={handleSubmit} apiError={apiError}>
        {(form) => (
          <>
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <input data-testid="name-input" placeholder="Name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <button type="submit">Save</button>
          </>
        )}
      </Form>
    );

    expect(await screen.findByText(/Server-side validation failed./i)).toBeInTheDocument();
    expect(screen.getByText(/Please fix the highlighted fields/)).toBeInTheDocument();
  });
});
