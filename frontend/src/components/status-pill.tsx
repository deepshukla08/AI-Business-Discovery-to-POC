"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";

export default function StatusPill() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    api
      .health()
      .then(() => setOk(true))
      .catch(() => setOk(false));
  }, []);

  const label = ok === null ? "checking…" : ok ? "online" : "offline";
  // monochrome: filled dot means connected, hollow means not
  const dot = ok ? "bg-ink" : "border border-muted";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-3 py-1 text-xs text-muted">
      <span className={`h-1.5 w-1.5 rounded-full ${dot}`} />
      {label}
    </span>
  );
}
