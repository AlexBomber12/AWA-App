"use client";

import type { Rule } from "@/lib/api/decisionClient";

import { type KeyboardEvent } from "react";

import { Button } from "@/components/ui";
import { cn } from "@/lib/utils";

type DecisionRulesListProps = {
  rules: Rule[];
  isLoading?: boolean;
  selectedRuleId?: string | null;
  onSelectRule: (ruleId: string) => void;
  onToggleRule: (rule: Rule, nextActive: boolean) => void;
  canConfigure?: boolean;
  togglingRuleId?: string | null;
  isMutatingRule?: boolean;
};

const formatDate = (value: string) =>
  new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(value));

export function DecisionRulesList({
  rules,
  isLoading,
  selectedRuleId,
  onSelectRule,
  onToggleRule,
  canConfigure = false,
  togglingRuleId,
  isMutatingRule,
}: DecisionRulesListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={`rule-skeleton-${index}`} className="h-24 animate-pulse rounded-xl border border-border bg-muted/40" />
        ))}
      </div>
    );
  }

  if (!rules.length) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-muted/20 p-6 text-sm text-muted-foreground">
        No rules configured yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {rules.map((rule) => {
        const isSelected = rule.id === selectedRuleId;
        const isToggling = togglingRuleId === rule.id;
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
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {rule.scope}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
              <p>
                Created {formatDate(rule.createdAt)} · Updated {formatDate(rule.updatedAt)}
              </p>
              <Button
                variant="outline"
                size="sm"
                onClick={(event) => {
                  event.stopPropagation();
                  onToggleRule(rule, !rule.active);
                }}
                disabled={!canConfigure || (isMutatingRule && !isToggling)}
                isLoading={isToggling}
              >
                {rule.active ? "Pause" : "Activate"}
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
