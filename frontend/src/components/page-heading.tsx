export function PageHeading({
  eyebrow,
  title,
  description,
}: {
  description: string;
  eyebrow: string;
  title: string;
}) {
  return (
    <div className="mb-7">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-sky-300">
        {eyebrow}
      </div>
      <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">
        {title}
      </h1>
      <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
        {description}
      </p>
    </div>
  );
}
