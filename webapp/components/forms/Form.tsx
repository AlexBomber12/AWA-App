"use client";

import * as React from "react";
import { zodResolver } from "@hookform/resolvers/zod";
import {
  Controller,
  type ControllerProps,
  FormProvider,
  type FieldPath,
  type FieldValues,
  type SubmitErrorHandler,
  type UseFormReturn,
  useForm,
  useFormContext,
} from "react-hook-form";
import { Slot } from "@radix-ui/react-slot";
import { createContext, useContext, type ReactNode, useEffect, useId, useState } from "react";
import type { z } from "zod";

import type { ApiError } from "@/lib/api/fetchFromApi";
import { cn } from "@/lib/utils";

type FormProps<TFieldValues extends FieldValues> = {
  schema: z.ZodType<TFieldValues, z.ZodTypeDef, TFieldValues>;
  defaultValues: TFieldValues;
  children: (form: UseFormReturn<TFieldValues>) => ReactNode;
  onSubmit: (values: TFieldValues) => void | Promise<void>;
  onError?: SubmitErrorHandler<TFieldValues>;
  apiError?: ApiError | null;
  id?: string;
  className?: string;
};

type FieldErrorRecord = Record<string, string>;

const extractFieldErrors = (details: unknown): FieldErrorRecord | null => {
  if (!details || typeof details !== "object") {
    return null;
  }

  if ("fieldErrors" in details && typeof details.fieldErrors === "object" && details.fieldErrors) {
    return details.fieldErrors as FieldErrorRecord;
  }

  const entries = Object.entries(details as Record<string, unknown>);
  if (entries.every(([, value]) => typeof value === "string")) {
    return details as FieldErrorRecord;
  }

  return null;
};

const FormErrorAlert = ({ message }: { message: string }) => (
  <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-900 dark:border-red-900/40 dark:bg-red-900/30 dark:text-red-100">
    {message}
  </div>
);

export function Form<TFieldValues extends FieldValues>({
  schema,
  defaultValues,
  children,
  onSubmit,
  onError,
  apiError = null,
  id,
  className,
}: FormProps<TFieldValues>) {
  const form = useForm<TFieldValues>({
    resolver: zodResolver(schema),
    defaultValues,
    mode: "onSubmit",
  });

  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    form.clearErrors();
    if (!apiError) {
      setFormError(null);
      return;
    }

    const fieldErrors = extractFieldErrors(apiError.details);
    if (fieldErrors) {
      Object.entries(fieldErrors).forEach(([field, errorMessage]) => {
        form.setError(field as FieldPath<TFieldValues>, {
          type: "server",
          message: errorMessage,
        });
      });
      setFormError(apiError.message ?? "Please review the highlighted fields.");
    } else {
      setFormError(apiError.message);
    }
  }, [apiError, form]);

  const handleSubmit = form.handleSubmit(
    async (values) => {
      setFormError(null);
      await onSubmit(values);
    },
    (errors) => {
      onError?.(errors);
    }
  );

  return (
    <FormProvider {...form}>
      <form id={id} className={cn("space-y-6", className)} onSubmit={handleSubmit}>
        {formError ? <FormErrorAlert message={formError} /> : null}
        {children(form)}
      </form>
    </FormProvider>
  );
}

// The following primitives mirror shadcn/ui's composition helpers.

const FormFieldContext = createContext<{ name: string } | undefined>(undefined);

export const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>,
>({
  ...props
}: ControllerProps<TFieldValues, TName>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

export const useFormField = () => {
  const fieldContext = useContext(FormFieldContext);
  const itemContext = useContext(FormItemContext);
  const { getFieldState, formState } = useFormContext();

  if (!fieldContext) {
    throw new Error("useFormField should be used within <FormField>");
  }

  const fieldState = getFieldState(fieldContext.name, formState);

  return {
    id: itemContext?.id,
    name: fieldContext.name,
    formItemId: itemContext?.id,
    formDescriptionId: itemContext?.descriptionId,
    formMessageId: itemContext?.messageId,
    ...fieldState,
  };
};

const FormItemContext = createContext<{
  id: string;
  descriptionId?: string;
  messageId?: string;
} | null>(null);

export const FormItem = ({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) => {
  const id = useId();
  const descriptionId = `${id}-description`;
  const messageId = `${id}-message`;
  return (
    <FormItemContext.Provider value={{ id, descriptionId, messageId }}>
      <div className={cn("space-y-1.5", className)} {...props} />
    </FormItemContext.Provider>
  );
};

export const FormLabel = ({ className, ...props }: React.ComponentPropsWithoutRef<"label">) => {
  const { error, formItemId } = useFormField();
  return (
    <label
      className={cn("text-sm font-medium leading-none peer-disabled:cursor-not-allowed", error ? "text-red-600" : undefined, className)}
      htmlFor={formItemId}
      {...props}
    />
  );
};

export const FormControl = React.forwardRef<
  React.ElementRef<typeof Slot>,
  React.ComponentPropsWithoutRef<typeof Slot>
>(({ className, ...props }, ref) => {
  const { formItemId, formDescriptionId, formMessageId, error } = useFormField();
  return (
    <Slot
      ref={ref}
      id={formItemId}
      aria-describedby={[formDescriptionId, formMessageId].filter(Boolean).join(" ") || undefined}
      aria-invalid={error ? "true" : "false"}
      className={className}
      {...props}
    />
  );
});
FormControl.displayName = "FormControl";

export const FormDescription = ({ className, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => {
  const { formDescriptionId } = useFormField();
  return (
    <p id={formDescriptionId} className={cn("text-sm text-muted-foreground", className)} {...props} />
  );
};

export const FormMessage = ({ className, children, ...props }: React.HTMLAttributes<HTMLParagraphElement>) => {
  const { formMessageId, error } = useFormField();
  const body = error ? (error.message ?? children) : children;
  if (!body) {
    return null;
  }
  return (
    <p id={formMessageId} className={cn("text-sm text-red-600", className)} {...props}>
      {body}
    </p>
  );
};
