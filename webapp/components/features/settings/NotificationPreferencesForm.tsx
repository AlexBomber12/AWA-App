"use client";

import { useState } from "react";
import { z } from "zod";

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/forms";
import { Button, Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";
import type { ApiError } from "@/lib/api/fetchFromApi";

const notificationSchema = z.object({
  contactEmail: z.string().email("Please enter a valid email."),
  digestCadence: z.enum(["daily", "weekly", "off"]),
  escalationChannel: z.string().min(3, "Escalation channel is required."),
});

type NotificationSettings = z.infer<typeof notificationSchema>;

const DEFAULT_VALUES: NotificationSettings = {
  contactEmail: "ops@example.com",
  digestCadence: "weekly",
  escalationChannel: "#ops-alerts",
};

export function NotificationPreferencesForm() {
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const [status, setStatus] = useState<"idle" | "saving" | "success">("idle");

  const handleSubmit = async (values: NotificationSettings) => {
    setStatus("saving");
    await new Promise((resolve) => setTimeout(resolve, 500));

    if (!values.contactEmail.endsWith("@example.com")) {
      setApiError({
        code: "VALIDATION_ERROR",
        message: "Please fix the highlighted fields.",
        status: 422,
        details: {
          fieldErrors: {
            contactEmail: "Use your @example.com address to receive notifications.",
          },
        },
      });
      setStatus("idle");
      return;
    }

    setApiError(null);
    setStatus("success");
  };

  const handleError = () => {
    setStatus("idle");
  };

  return (
    <div className="rounded-xl border border-border bg-background/80 p-6 shadow-sm">
      <Form schema={notificationSchema} defaultValues={DEFAULT_VALUES} onSubmit={handleSubmit} onError={handleError} apiError={apiError}>
        {(form) => (
          <>
            <FormField
              control={form.control}
              name="contactEmail"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contact email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="you@example.com" {...field} />
                  </FormControl>
                  <FormDescription>Used for SLA digests and ROI approvals.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="digestCadence"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Digest cadence</FormLabel>
                  <FormControl>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose cadence" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Daily summary</SelectItem>
                        <SelectItem value="weekly">Weekly digest</SelectItem>
                        <SelectItem value="off">Disable digests</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormDescription>Controls ROI + Returns snapshots delivered to your inbox.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="escalationChannel"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Escalation channel</FormLabel>
                  <FormControl>
                    <Input placeholder="#ops-alerts" {...field} />
                  </FormControl>
                  <FormDescription>Slack channel for ingestion or decisioning incidents.</FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="flex items-center justify-between">
              {status === "success" ? (
                <p className="text-sm text-green-600">Preferences saved. You can adjust any time.</p>
              ) : (
                <p className="text-sm text-muted-foreground">Changes apply immediately for your team.</p>
              )}
              <Button type="submit" isLoading={status === "saving"}>
                Save preferences
              </Button>
            </div>
          </>
        )}
      </Form>
    </div>
  );
}
