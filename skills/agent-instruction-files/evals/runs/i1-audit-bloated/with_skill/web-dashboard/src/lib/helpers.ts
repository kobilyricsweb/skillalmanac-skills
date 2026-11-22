export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', { timeZone: 'UTC' }).format(new Date(iso));
}
