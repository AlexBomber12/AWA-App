import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import { z } from "zod";

import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/forms";
import { Button, Input } from "@/components/ui";

const schema = z.object({
  name: z.string().min(1, "Name is required."),
  email: z.string().email("Use a valid email address."),
});

const meta: Meta = {
  title: "Forms/Form",
};

export default meta;

export const Basic: StoryObj = {
  render: () => {
    const [result, setResult] = useState<string | null>(null);
    return (
      <div className="max-w-md space-y-4 rounded-xl border border-border bg-background/80 p-6 shadow-sm">
        <Form
          schema={schema}
          defaultValues={{ name: "", email: "" }}
          onSubmit={async (values) => {
            setResult(`Saved ${values.name}`);
          }}
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
                      <Input placeholder="Jane Doe" {...field} />
                    </FormControl>
                    <FormDescription>Shown on approvals and audit history.</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input placeholder="jane@example.com" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {result ?? "Submit to preview success handling."}
                </p>
                <Button type="submit">Save</Button>
              </div>
            </>
          )}
        </Form>
      </div>
    );
  },
};
