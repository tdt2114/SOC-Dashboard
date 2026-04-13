"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export function LoginForm() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const payload = (await response.json()) as { detail?: string };
        const detail = payload.detail || "Login failed";
        if (detail.toLowerCase().includes("invalid")) {
          throw new Error("Invalid username or password.");
        }
        throw new Error("Unable to sign in right now.");
      }

      router.push("/alerts");
      router.refresh();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unknown login error");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="login-form" onSubmit={onSubmit} autoComplete="off" noValidate>
      <label>
        <span>Username</span>
        <div className="field-shell">
          <input
            name="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="Username"
            autoComplete="username"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            inputMode="text"
            required
          />
        </div>
      </label>

      <label>
        <span>Password</span>
        <div className="field-shell">
          <input
            name="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            placeholder="Password"
            autoComplete="current-password"
            autoCapitalize="none"
            autoCorrect="off"
            spellCheck={false}
            required
          />
        </div>
      </label>

      {error ? (
        <p className="form-error" role="alert" aria-live="polite">
          {error}
        </p>
      ) : null}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Signing In..." : "Sign In"}
      </button>
    </form>
  );
}
