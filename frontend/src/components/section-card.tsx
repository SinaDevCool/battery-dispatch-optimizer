import { cn } from "@/lib/utils";

export function SectionCard({
  children,
  className,
  title,
  action,
}: {
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  title: string;
}) {
  return (
    <section
      className={cn(
        "rounded-lg border border-slate-800 bg-slate-950/70 p-5 shadow-sm shadow-black/20",
        className,
      )}
    >
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-base font-semibold text-slate-100">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}
