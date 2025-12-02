"use client";

import type { Rule } from "@/lib/api/decisionClient";

import { type KeyboardEvent, useMemo } from "react";

import { cn } from "@/lib/utils";

type DecisionRulesListProps = {
  rules: Rule[];
  isLoading?: boolean;
  selectedRuleId?: string | null;
  onSelectRule: (ruleId: string) => void;
};

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));

const describeConditions = (rule: Rule) => {
  if (!rule.conditions.length) {
    return "No conditions";
  }
  return rule.conditions
    .map((condition) => {
      if (condition.expression) {
        return condition.expression;
      }
      if (condition.category) {
        return `Category: ${condition.category}`;
      }
      if (condition.vendorId) {
        return `Vendor ${condition.vendorId}`;
      }
      const op = condition.op ?? (condition as { operator?: string }).operator;
      if (condition.field && op) {
        return `${condition.field} ${op} ${condition.value}`;
      }
      return "Condition";
    })
    .join(" · ");
};

const describeActions = (rule: Rule) => {
  if (!rule.actions || rule.actions.length === 0) {
    return "No actions";
  }
  return rule.actions.map((action) => action.action.replaceAll("_", " ")).join(", ");
};

export function DecisionRulesList({ rules, isLoading, selectedRuleId, onSelectRule }: DecisionRulesListProps) {
  const safeRules = useMemo(() => rules ?? [], [rules]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={`rule-skeleton-${index}`} className="h-28 animate-pulse rounded-xl border border-border bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!safeRules.length) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/20 p-6 text-sm text-muted-foreground">
        No rules configured yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {safeRules.map((rule) => {
        const isSelected = rule.id === selectedRuleId;
        const handleKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            onSelectRule(rule.id);
          }
        };

        return (
          <div
            key={rule.id}
            role="button"
            tabIndex={0}
            onClick={() => onSelectRule(rule.id)}
            onKeyDown={handleKeyDown}
            className={cn(
              "w-full rounded-2xl border px-4 py-3 text-left transition-colors",
              isSelected ? "border-brand bg-brand/5" : "border-border hover:bg-muted/30"
            )}
          >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-base font-semibold">{rule.name}</p>
                  <p className="text-sm text-muted-foreground">{rule.description ?? "No description provided."}</p>
                </div>
                <div className="flex flex-col items-end gap-2 text-xs font-semibold uppercase">
                  <span className="rounded-full bg-muted px-3 py-1 tracking-wide text-muted-foreground">{rule.scope}</span>
                  <span
                    className={cn(
                      "rounded-full px-3 py-1 tracking-wide",
                      (rule.enabled ?? (rule as { isActive?: boolean }).isActive ?? false)
                        ? "bg-emerald-100 text-emerald-900"
                        : "bg-zinc-200 text-zinc-900"
                    )}
                  >
                    {(rule.enabled ?? (rule as { isActive?: boolean }).isActive ?? false) ? "Active" : "Disabled"}
                  </span>
                </div>
              </div>
            <div className="mt-3 space-y-1 text-xs text-muted-foreground">
              <p>
                <span className="font-semibold text-foreground">Conditions:</span> {describeConditions(rule)}
              </p>
              <p>
                <span className="font-semibold text-foreground">Actions:</span> {describeActions(rule)}
              </p>
              <p>
                Created {formatDate(rule.createdAt)} · Updated {formatDate(rule.updatedAt)}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
