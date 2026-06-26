import { Loader2 } from "lucide-react";

export default function TabLoader({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-emerald-600 gap-3">
      <Loader2 className="w-6 h-6 animate-spin" />
      <p className="text-sm text-gray-400">{label}</p>
    </div>
  );
}
