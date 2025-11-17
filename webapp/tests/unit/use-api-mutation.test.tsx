import { type ReactElement } from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import type { ApiError } from "@/lib/api/apiError";
import { useApiMutation } from "@/lib/api/useApiMutation";

const user = userEvent.setup();

const renderWithClient = (ui: ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      mutations: { retry: 0 },
    },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
};

describe("useApiMutation", () => {
  it("executes the mutation and resolves callbacks", async () => {
    const mutateFn = jest.fn().mockResolvedValue({ ok: true });
    const onSuccess = jest.fn();

    const Harness = () => {
      const mutation = useApiMutation({
        mutationFn: mutateFn,
        onSuccess,
      });

      return (
        <button data-testid="mutate" onClick={() => mutation.mutate({ asin: "ASIN-42" })}>
          Run mutation
        </button>
      );
    };

    renderWithClient(<Harness />);

    await user.click(screen.getByTestId("mutate"));

    await waitFor(() => expect(mutateFn).toHaveBeenCalledWith({ asin: "ASIN-42" }, expect.anything()));
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("bubbles ApiError instances through onError", async () => {
    const apiError: ApiError = {
      code: "BFF_ERROR",
      message: "simulated failure",
      status: 500,
    };
    const mutateFn = jest.fn().mockRejectedValue(apiError);
    const onError = jest.fn();
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => undefined);

    const Harness = () => {
      const mutation = useApiMutation({
        mutationFn: mutateFn,
        onError,
      });

      return (
        <button data-testid="mutate" onClick={() => mutation.mutate({ asin: "ASIN-99" })}>
          Run mutation
        </button>
      );
    };

    renderWithClient(<Harness />);
    await user.click(screen.getByTestId("mutate"));

    await waitFor(() => expect(onError).toHaveBeenCalledWith(apiError, { asin: "ASIN-99" }, undefined, expect.anything()));
    expect(consoleSpy).toHaveBeenCalled();
    consoleSpy.mockRestore();
  });
});
