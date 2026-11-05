import "server-only";

import { redirect } from "next/navigation";

import { getSession, type AppSession } from "./auth";

export async function requireSession(): Promise<NonNullable<AppSession>> {
  const sessionData = await getSession();
  if (!sessionData) {
    redirect("/login");
  }
  return sessionData;
}