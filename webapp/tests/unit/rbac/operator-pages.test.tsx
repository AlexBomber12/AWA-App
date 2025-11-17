import { render, screen } from "@testing-library/react";
import type { Session } from "next-auth";
import React from "react";

import InboxRoutePage from "@/app/inbox/page";
import DecisionRoutePage from "@/app/decision/page";
import { InboxPage } from "@/components/features/inbox/InboxPage";
import { DecisionEnginePage } from "@/components/features/decision/DecisionEnginePage";
import { getServerAuthSession } from "@/lib/auth";

jest.mock("@/lib/auth", () => ({
  getServerAuthSession: jest.fn(),
}));

const mockGetServerAuthSession = getServerAuthSession as jest.MockedFunction<typeof getServerAuthSession>;

const buildSession = (roles: string[]): Session => ({
  user: {
    name: "Tester",
    email: "tester@example.com",
    roles,
  },
  expires: "",
});

describe("Operator page RBAC", () => {
  afterEach(() => {
    mockGetServerAuthSession.mockReset();
  });

  it("renders not allowed message for viewer navigating to Inbox", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(["viewer"]));
    const result = await InboxRoutePage();
    render(result as React.ReactElement);
    expect(screen.getByText(/Not allowed/i)).toBeInTheDocument();
  });

  it("returns InboxPage component for ops role", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(["ops"]));
    const result = (await InboxRoutePage()) as React.ReactElement;
    expect(result.type).toBe(InboxPage);
  });

  it("renders not allowed message for viewer navigating to Decision Engine", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(["viewer"]));
    const result = await DecisionRoutePage();
    render(result as React.ReactElement);
    expect(screen.getByText(/Not allowed/i)).toBeInTheDocument();
  });

  it("blocks decision engine for ops role", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(["ops"]));
    const result = await DecisionRoutePage();
    render(result as React.ReactElement);
    expect(screen.getByText(/Not allowed/i)).toBeInTheDocument();
  });

  it("returns DecisionEnginePage component for admin role", async () => {
    mockGetServerAuthSession.mockResolvedValue(buildSession(["admin"]));
    const result = (await DecisionRoutePage()) as React.ReactElement;
    expect(result.type).toBe(DecisionEnginePage);
  });
});
