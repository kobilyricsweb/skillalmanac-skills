/* DO NOT EDIT: generated from openapi.yaml */
/* Regenerate with: npm run generate */

export interface User {
  id: string;
  email: string;
  displayName?: string;
}

export async function getUser(baseUrl: string, id: string): Promise<User> {
  const res = await fetch(`${baseUrl}/users/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`getUser failed with status ${res.status}`);
  }
  return (await res.json()) as User;
}
