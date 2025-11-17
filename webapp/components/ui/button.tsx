"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        primary: "bg-brand text-brand-foreground shadow hover:bg-brand/90",
        secondary: "bg-muted text-foreground hover:bg-muted/70",
        outline: "border border-input bg-background text-foreground hover:bg-muted/60",
        destructive: "bg-red-600 text-white hover:bg-red-600/90",
        ghost: "text-foreground hover:bg-muted/60",
        default: "bg-brand text-brand-foreground shadow hover:bg-brand/90",
      },
      size: {
        sm: "h-8 rounded-md px-3 text-sm",
        md: "h-10 rounded-md px-4 text-sm",
        lg: "h-11 rounded-lg px-6 text-base",
        icon: "h-10 w-10",
        default: "h-10 rounded-md px-4 text-sm",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

type LoadingSpinnerProps = {
  className?: string;
};

const LoadingSpinner = ({ className }: LoadingSpinnerProps) => (
  <span
    className={cn(
      "inline-flex size-4 animate-spin rounded-full border-2 border-current border-t-transparent",
      className
    )}
    aria-hidden="true"
  />
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, isLoading = false, disabled, children, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    const isDisabled = disabled ?? false;
    return (
      <Comp
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        disabled={isDisabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            <LoadingSpinner />
            <span className="sr-only">Loading</span>
          </>
        ) : null}
        <span className={cn(isLoading ? "opacity-70" : undefined)}>{children}</span>
      </Comp>
    );
  }
);
Button.displayName = "Button";
