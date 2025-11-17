import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";

import { Input, Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui";

const meta: Meta = {
  title: "UI/Inputs",
};

export default meta;

export const InputsShowcase: StoryObj = {
  render: () => {
    const [value, setValue] = useState("pending");
    return (
      <div className="space-y-4 p-6">
        <Input placeholder="Type to search" />
        <Input placeholder="Disabled field" disabled />
        <Select value={value} onValueChange={setValue}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="approved">Approved</SelectItem>
          </SelectContent>
        </Select>
      </div>
    );
  },
};
