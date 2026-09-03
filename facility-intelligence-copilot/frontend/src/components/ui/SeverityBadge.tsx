export function SeverityBadge({ severity }: { severity: string }) {
  const sev = (severity || 'INFO').toUpperCase();
  let colorStyle = 'bg-zinc-100 text-zinc-700 border-zinc-200';

  if (sev === 'CRITICAL') {
    colorStyle = 'bg-rose-50 text-rose-800 border-rose-200';
  } else if (sev === 'HIGH') {
    colorStyle = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (sev === 'WARNING') {
    colorStyle = 'bg-amber-50 text-amber-800 border-amber-200';
  } else if (sev === 'INFO') {
    colorStyle = 'bg-zinc-100 text-zinc-700 border-zinc-200';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border ${colorStyle}`}>
      {sev}
    </span>
  );
}

export function HealthBadge({ score }: { score: number }) {
  let style = 'bg-emerald-50 text-emerald-800 border-emerald-200';
  if (score < 70) {
    style = 'bg-rose-50 text-rose-800 border-rose-200';
  } else if (score < 85) {
    style = 'bg-amber-50 text-amber-800 border-amber-200';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${style}`}>
      {score}%
    </span>
  );
}
