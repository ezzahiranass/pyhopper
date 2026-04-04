import * as React from "react";
import { Check } from "lucide-react";

import { cn } from "@/lib/utils";

type CheckboxProps = Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "onChange"> & {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
};

const Checkbox = React.forwardRef<HTMLButtonElement, CheckboxProps>(
  ({ className, checked = false, disabled, onCheckedChange, ...props }, ref) => {
    return (
      <button
        ref={ref}
        type="button"
        role="checkbox"
        aria-checked={checked}
        disabled={disabled}
        data-state={checked ? "checked" : "unchecked"}
        className={cn(
          "peer inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border border-input bg-background text-transparent shadow-sm transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:border-foreground data-[state=checked]:bg-foreground data-[state=checked]:text-background",
          className,
        )}
        onClick={() => {
          if (disabled) return;
          onCheckedChange?.(!checked);
        }}
        {...props}
      >
        <Check className="h-3 w-3" strokeWidth={3} />
      </button>
    );
  },
);

Checkbox.displayName = "Checkbox";

export { Checkbox };
