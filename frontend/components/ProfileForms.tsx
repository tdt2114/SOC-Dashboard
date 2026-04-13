"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { AuthUser } from "@/lib/types";

export function ProfileForms({ currentUser }: { currentUser: AuthUser }) {
  const router = useRouter();
  const [email, setEmail] = useState(currentUser.email);
  const [fullName, setFullName] = useState(currentUser.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [profileMessage, setProfileMessage] = useState<string | null>(null);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  async function submitProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setProfileError(null);
    setProfileMessage(null);
    setIsSavingProfile(true);

    try {
      const response = await fetch("/api/auth/me", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email,
          full_name: fullName || null
        })
      });

      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to update profile");
      }

      setProfileMessage("Profile updated.");
      router.refresh();
    } catch (error) {
      setProfileError(error instanceof Error ? error.message : "Unable to update profile");
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function submitPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordMessage(null);
    setIsSavingPassword(true);

    try {
      const response = await fetch("/api/auth/change-password", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      const payload = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        throw new Error(payload?.detail || "Unable to change password");
      }

      setCurrentPassword("");
      setNewPassword("");
      setPasswordMessage("Password changed.");
    } catch (error) {
      setPasswordError(error instanceof Error ? error.message : "Unable to change password");
    } finally {
      setIsSavingPassword(false);
    }
  }

  return (
    <div className="profile-grid">
      <section className="panel stack">
        <div className="panel-header">
          <div>
            <h3>Account Profile</h3>
            <p>Review and update your account details.</p>
          </div>
        </div>
        <div className="key-value-grid">
          <div className="key-value-item">
            <span className="key-label">Username</span>
            <div className="key-value">{currentUser.username}</div>
          </div>
          <div className="key-value-item">
            <span className="key-label">Department</span>
            <div className="key-value">{currentUser.department || "N/A"}</div>
          </div>
          <div className="key-value-item">
            <span className="key-label">Roles</span>
            <div className="key-value">{currentUser.roles.join(", ")}</div>
          </div>
          <div className="key-value-item">
            <span className="key-label">Access</span>
            <div className="key-value">{currentUser.is_superuser ? "Super Admin" : "Standard"}</div>
          </div>
        </div>
        <form className="stack-form" onSubmit={submitProfile}>
          <label>
            <span>Full Name</span>
            <input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
          </label>
          <label>
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email address"
              required
            />
          </label>
          {profileError ? <p className="form-error">{profileError}</p> : null}
          {profileMessage ? <p className="form-success">{profileMessage}</p> : null}
          <button type="submit" disabled={isSavingProfile}>
            {isSavingProfile ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </section>

      <section className="panel stack">
        <div className="panel-header">
          <div>
            <h3>Change Password</h3>
            <p>Update your current account password.</p>
          </div>
        </div>
        <form className="stack-form" onSubmit={submitPassword}>
          <label>
            <span>Current Password</span>
            <input
              type="password"
              value={currentPassword}
              onChange={(event) => setCurrentPassword(event.target.value)}
              placeholder="Current password"
              required
            />
          </label>
          <label>
            <span>New Password</span>
            <input
              type="password"
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="New password"
              minLength={8}
              required
            />
          </label>
          {passwordError ? <p className="form-error">{passwordError}</p> : null}
          {passwordMessage ? <p className="form-success">{passwordMessage}</p> : null}
          <button type="submit" disabled={isSavingPassword}>
            {isSavingPassword ? "Updating..." : "Change Password"}
          </button>
        </form>
      </section>
    </div>
  );
}
