"use client";

import { useRef, useState } from "react";
import type { UseFormReturn } from "react-hook-form";
import { z } from "zod";

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/forms";
import { Button, Input, Tabs, TabsList, TabsTrigger } from "@/components/ui";
import { Checkbox } from "@/components/ui/checkbox";
import type { ApiError } from "@/lib/api/apiError";
import { startIngestJob, type IngestJobStatus, type IngestStartRequest } from "@/lib/api/ingestClient";
import { useApiMutation } from "@/lib/api/useApiMutation";
import { cn } from "@/lib/utils";

const SOURCE_TYPES = ["file", "uri"] as const;
type SourceType = (typeof SOURCE_TYPES)[number];

const fileFieldSchema = z
  .custom<File | null>((value) => value === null || value instanceof File, {
    message: "Upload a CSV or XLSX file.",
  })
  .nullable()
  .optional();

const ingestSchema = z
  .object({
    sourceType: z.enum(SOURCE_TYPES),
    file: fileFieldSchema,
    uri: z
      .string()
      .optional()
      .transform((value) => (value ?? "").trim()),
    reportType: z
      .string()
      .optional()
      .transform((value) => (value ?? "").trim()),
    force: z.boolean().optional().default(false),
  })
  .superRefine((values, ctx) => {
    if (values.sourceType === "file") {
      const file = values.file;
      if (!file || !(file instanceof File) || file.size === 0) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Upload a CSV or XLSX file.",
          path: ["file"],
        });
      }
    } else {
      const uri = values.uri ?? "";
      if (!uri) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Enter the source URI to ingest.",
          path: ["uri"],
        });
        return;
      }
      try {
        // eslint-disable-next-line no-new
        new URL(uri);
      } catch {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: "Enter a valid URI (s3://… or https://…).",
          path: ["uri"],
        });
      }
    }
  });

type IngestFormValues = z.infer<typeof ingestSchema>;

const DEFAULT_VALUES: IngestFormValues = {
  sourceType: "file",
  file: null,
  uri: "",
  reportType: "",
  force: false,
};

type IngestJobFormProps = {
  onJobStarted?: (job: IngestJobStatus) => void;
  disabled?: boolean;
  className?: string;
};

export function IngestJobForm({ onJobStarted, disabled = false, className }: IngestJobFormProps) {
  const [apiError, setApiError] = useState<ApiError | null>(null);
  const formRef = useRef<UseFormReturn<IngestFormValues> | null>(null);

  const mutation = useApiMutation<IngestJobStatus, ApiError, IngestStartRequest>({
    mutationFn: (payload) => startIngestJob(payload),
  });

  const handleSubmit = async (values: IngestFormValues) => {
    setApiError(null);

    const payload: IngestStartRequest = {};
    if (values.reportType) {
      payload.report_type = values.reportType;
    }
    if (values.force) {
      payload.force = true;
    }
    if (values.sourceType === "file" && values.file instanceof File) {
      payload.file = values.file;
    }
    if (values.sourceType === "uri") {
      payload.uri = values.uri;
    }

    try {
      const job = await mutation.mutateAsync(payload);
      formRef.current?.reset(DEFAULT_VALUES);
      mutation.reset();
      onJobStarted?.(job);
    } catch (error) {
      setApiError(error as ApiError);
    }
  };

  const isSubmitting = mutation.isPending;
  const isDisabled = disabled || isSubmitting;

  return (
    <div className={cn("space-y-6", className)}>
      <Form schema={ingestSchema} defaultValues={DEFAULT_VALUES} onSubmit={handleSubmit} apiError={apiError}>
        {(form) => {
          formRef.current = form;
          const sourceType = form.watch("sourceType");

          const handleSourceTypeChange = (value: string) => {
            const nextValue = value as SourceType;
            form.setValue("sourceType", nextValue);
            if (nextValue === "file") {
              form.setValue("uri", "");
            } else {
              form.setValue("file", null);
            }
          };

          return (
            <div className="space-y-6">
              <div>
                <p className="text-sm font-medium text-muted-foreground">Select the ingest source.</p>
                <Tabs value={sourceType} onValueChange={handleSourceTypeChange} className="mt-3">
                  <TabsList className="grid grid-cols-2">
                    <TabsTrigger value="file" disabled={isDisabled}>
                      Upload file
                    </TabsTrigger>
                    <TabsTrigger value="uri" disabled={isDisabled}>
                      Remote URI
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>

              {sourceType === "file" ? (
                <FormField
                  control={form.control}
                  name="file"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>CSV or XLSX file</FormLabel>
                      <FormControl>
                        <Input
                          type="file"
                          accept=".csv,.xlsx,.xls"
                          disabled={isDisabled}
                          onChange={(event) => {
                            const nextFile = event.target.files?.[0] ?? null;
                            field.onChange(nextFile);
                          }}
                        />
                      </FormControl>
                      <FormDescription>Upload exports from Vendor Central or agent output bundles.</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ) : (
                <FormField
                  control={form.control}
                  name="uri"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Source URI</FormLabel>
                      <FormControl>
                        <Input
                          placeholder="s3://bucket/path/report.csv or https://…"
                          disabled={isDisabled}
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>Provide a URI reachable by the ingest workers (S3, MinIO, HTTPS).</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              <FormField
                control={form.control}
                name="reportType"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Report type</FormLabel>
                    <FormControl>
                      <Input placeholder="returns_report" disabled={isDisabled} {...field} />
                    </FormControl>
                    <FormDescription>Optional hint for the ETL agent (returns_report, keepa_ingestor, etc.).</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="force"
                render={({ field }) => (
                  <FormItem className="flex flex-row items-start gap-3 space-y-0 rounded-lg border border-border/70 p-4">
                    <FormControl>
                      <Checkbox
                        checked={field.value}
                        onChange={(event) => field.onChange(event.target.checked)}
                        disabled={isDisabled}
                      />
                    </FormControl>
                    <div className="space-y-0.5">
                      <FormLabel>Force replay</FormLabel>
                      <FormDescription>
                        Override idempotency guards if the source needs a fresh reprocess.
                      </FormDescription>
                    </div>
                  </FormItem>
                )}
              />

              <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-sm text-muted-foreground">
                  Jobs enter the Celery ingest queue; status updates will appear in the list below.
                </p>
                <Button type="submit" isLoading={isSubmitting} disabled={isDisabled}>
                  Start ingest job
                </Button>
              </div>
            </div>
          );
        }}
      </Form>
    </div>
  );
}
