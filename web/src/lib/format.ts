export function formatTimestamp(seconds: number): string {
  const roundedSeconds = Math.max(0, Math.round(seconds));
  const minutes = Math.floor(roundedSeconds / 60);
  const remainder = roundedSeconds % 60;

  return `${minutes}:${remainder.toString().padStart(2, "0")}`;
}
