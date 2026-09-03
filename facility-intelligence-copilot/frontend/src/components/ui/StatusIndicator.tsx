export function StatusIndicator({ status }: { status: string }) {
  const s = (status || 'UNKNOWN').toUpperCase();
  let dotColor = 'bg-zinc-400';
  let textColor = 'text-zinc-600';

  if (s === 'HEALTHY' || s === 'OPEN' || s === 'READY' || s === 'OK' || s === 'RESOLVED') {
    dotColor = 'bg-emerald-500';
    textColor = 'text-emerald-800';
  } else if (s === 'WARNING' || s === 'ACKNOWLEDGED') {
    dotColor = 'bg-amber-500';
    textColor = 'text-amber-800';
  } else if (s === 'CRITICAL' || s === 'ERROR' || s === 'UNAVAILABLE') {
    dotColor = 'bg-rose-500';
    textColor = 'text-rose-800';
  }

  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-mono">
      <span className={`w-2 h-2 rounded-full ${dotColor}`} />
      <span className={textColor}>{s}</span>
    </span>
  );
}
