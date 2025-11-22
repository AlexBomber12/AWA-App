import {
  formatDecisionLabel,
  formatTaskDate,
  formatTaskEntity,
  formatTaskPriority,
  formatTaskSource,
  formatTaskState,
  reasonToText,
  taskPriorityStyle,
} from "@/components/features/inbox/taskFormatters";

describe("taskFormatters", () => {
  it("maps priorities to styles and labels", () => {
    expect(taskPriorityStyle(95)).toContain("rose");
    expect(taskPriorityStyle(75)).toContain("amber");
    expect(taskPriorityStyle(45)).toContain("sky");
    expect(taskPriorityStyle(10)).toContain("emerald");
    expect(taskPriorityStyle("critical")).toContain("rose");
  });

  it("formats priorities and states", () => {
    expect(formatTaskPriority(92)).toBe("Critical");
    expect(formatTaskPriority(72)).toBe("High");
    expect(formatTaskPriority(55)).toBe("Medium");
    expect(formatTaskPriority(5)).toBe("Low");
    expect(formatTaskPriority("in_progress")).toBe("in progress");

    expect(formatTaskState("snoozed")).toBe("Snoozed");
    expect(formatTaskState("blocked")).toBe("Blocked");
  });

  it("formats sources and dates", () => {
    expect(formatTaskSource("email")).toBe("Inbox email");
    expect(formatTaskSource("system")).toBe("System");
    expect(formatTaskSource("custom" as any)).toBe("custom");

    expect(formatTaskDate("2025-01-15T13:30:00Z", false)).toMatch(/Jan/);
    expect(formatTaskDate(null)).toBe("—");
    expect(formatTaskDate("invalid")).toBe("—");
  });

  it("formats entities", () => {
    expect(formatTaskEntity({ type: "sku", asin: "A-1", label: "Label" } as any)).toBe("Label (A-1)");
    expect(
      formatTaskEntity({ type: "sku_vendor", asin: "A-2", vendorId: "V-1" } as any)
    ).toBe("A-2 · Vendor V-1");
    expect(formatTaskEntity({ type: "vendor", vendorId: "V-2" } as any)).toBe("Vendor V-2");
    expect(formatTaskEntity({ type: "thread", threadId: "T-1" } as any)).toBe("T-1");
    expect(formatTaskEntity({ type: "price_list", id: "PL-1" } as any)).toBe("PL-1");
    expect(formatTaskEntity({ type: "unknown" } as any)).toBe("Unknown entity");
  });

  it("formats decisions and reasons", () => {
    expect(formatDecisionLabel("needs_review")).toBe("needs review");
    expect(reasonToText("manual review")).toBe("manual review");
    expect(reasonToText({ title: "Quota exceeded", detail: "retry later" } as any)).toBe(
      "Quota exceeded: retry later"
    );
    expect(reasonToText({ title: "Quota exceeded" } as any)).toBe("Quota exceeded");
  });
});
