"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

export type AuthMode = "login" | "register";

type AuthFormProps = {
  mode: AuthMode;
};

export default function AuthForm({ mode }: AuthFormProps) {
  const router = useRouter();
  const isRegister = mode === "register";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
      setError("Username is required");
      return;
    }
    if (password === "") {
      setError("Password cannot be blank");
      return;
    }
    setSubmitting(true);
    try {
      const response = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: trimmedUsername, password }),
        credentials: "same-origin",
      });
      let body: { error?: string } = {};
      try {
        body = (await response.json()) as { error?: string };
      } catch {
        body = {};
      }
      if (response.ok) {
        router.push("/dashboard");
        return;
      }
      setError(body.error ?? "Authentication failed");
      setSubmitting(false);
    } catch {
      setError("Network error — is the server running?");
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-copy">
        <span className="eyebrow">{isRegister ? "Create account" : "Welcome back"}</span>
        <h2>{isRegister ? "Start organizing your day" : "Stay on top of what matters"}</h2>
      </div>

      <form
        onSubmit={onSubmit}
        aria-label={isRegister ? "Register" : "Log in"}
        className="auth-form"
      >
        {error ? (
          <p role="alert" className="error">
            {error}
          </p>
        ) : null}

        <label className="field-label">
          <span>Username</span>
          <input
            type="text"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            autoComplete="username"
            placeholder="Enter your username"
          />
        </label>

        <label className="field-label">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            autoComplete={isRegister ? "new-password" : "current-password"}
            placeholder="Enter your password"
          />
        </label>

        <button type="submit" className="button-primary" disabled={submitting}>
          {isRegister ? "Register" : "Log in"}
        </button>
      </form>

      <p className="auth-switch">
        {isRegister ? "Already have an account?" : "Need an account?"}{" "}
        <Link href={isRegister ? "/login" : "/register"}>
          {isRegister ? "Log in" : "Create one"}
        </Link>
      </p>
    </div>
  );
}