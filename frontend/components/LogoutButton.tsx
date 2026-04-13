"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export function LogoutButton() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onLogout() {
    setIsSubmitting(true);
    try {
      await fetch("/api/auth/logout", {
        method: "POST"
      });
      router.push("/login");
      router.refresh();
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <button type="button" className="logout-button" onClick={onLogout} disabled={isSubmitting}>
      {isSubmitting ? "Signing Out..." : "Sign Out"}
    </button>
  );
}
