import { redirect } from "next/navigation";

import AuthForm from "../../components/AuthForm";
import { getSession } from "../../lib/auth";

export default async function RegisterPage() {
  let isAuthenticated = false;
  try {
    isAuthenticated = (await getSession()) !== null;
  } catch {
    isAuthenticated = false;
  }

  if (isAuthenticated) {
    redirect("/dashboard");
  }

  return (
    <main className="auth-page">
      <AuthForm mode="register" />
    </main>
  );
}
