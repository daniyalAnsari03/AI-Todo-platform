import "server-only";

import { headers } from "next/headers";

import { auth } from "../../auth";

export type AppSession = {
  session: { id: string; expiresAt: Date };
  user: { id: string; name: string; email: string };
} | null;

export async function getSession(): Promise<AppSession> {
  const requestHeaders = await headers();
  const session = await auth.api.getSession({ headers: requestHeaders });
  if (!session) {
    return null;
  }
  return {
    session: { id: session.session.id, expiresAt: session.session.expiresAt },
    user: {
      id: session.user.id,
      name: session.user.name,
      email: session.user.email,
    },
  };
}

export const session = getSession;