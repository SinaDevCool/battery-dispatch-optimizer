import { AlertTriangle } from "lucide-react";

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-400/30 bg-amber-400/10 p-4 text-sm text-amber-100">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div>{message}</div>
    </div>
  );
}
