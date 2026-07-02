const COOLDOWN_MS = 60_000;

export function canResend(key: string): boolean {
  const last = Number(localStorage.getItem(key) || 0);
  return Date.now() - last >= COOLDOWN_MS;
}

export function secondsUntilResend(key: string): number {
  const last = Number(localStorage.getItem(key) || 0);
  const remaining = COOLDOWN_MS - (Date.now() - last);
  return Math.max(0, Math.ceil(remaining / 1000));
}

export function markResent(key: string): void {
  localStorage.setItem(key, String(Date.now()));
}
