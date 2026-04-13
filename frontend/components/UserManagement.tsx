"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { DepartmentOption, RoleOption, UserAdminItem } from "@/lib/types";

function useModalBehavior(isOpen: boolean, onClose: () => void) {
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose]);
}

function UserCreateModal({
  departments,
  roles,
  onClose
}: {
  departments: DepartmentOption[];
  roles: RoleOption[];
  onClose: () => void;
}) {
  useModalBehavior(true, onClose);

  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [departmentId, setDepartmentId] = useState("");
  const [role, setRole] = useState(roles[0]?.name || "viewer");
  const [isActive, setIsActive] = useState(true);
  const [isSuperuser, setIsSuperuser] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleRoleChange(nextRole: string) {
    setRole(nextRole);
    if (nextRole !== "admin") {
      setIsSuperuser(false);
    }
  }

  function handleSuperadminChange(checked: boolean) {
    if (checked) {
      setRole("admin");
    }
    setIsSuperuser(checked);
  }

  async function createUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSubmitting(true);

    try {
      const response = await fetch("/api/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          password,
          full_name: fullName || null,
          department_id: departmentId ? Number(departmentId) : null,
          is_active: isActive,
          is_superuser: isSuperuser,
          roles: [role]
        })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to create user");
      }

      setMessage("User created.");
      router.refresh();
      onClose();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to create user");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Create New User</h3>
            <p style={{ margin: "0.2rem 0 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Provision a new account for an analyst or admin.
            </p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form className="stack-form" onSubmit={createUser}>
          <div className="admin-grid">
            <label>
              <span>Username</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} required />
            </label>
            <label>
              <span>Email</span>
              <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
            </label>
            <label>
              <span>Full Name</span>
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </label>
            <label>
              <span>Temporary Password</span>
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                minLength={8}
                required
              />
            </label>
            <label>
              <span>Department</span>
              <select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
                <option value="">No department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Role</span>
              <select value={role} onChange={(event) => handleRoleChange(event.target.value)}>
                {roles.map((item) => (
                  <option key={item.id} value={item.name}>{item.name}</option>
                ))}
              </select>
              <small className="field-hint">Role controls what the user can do inside the dashboard.</small>
            </label>
          </div>

          <div className="toggle-row">
            <label className="toggle">
              <input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
              <span>Active</span>
            </label>
            <label className="toggle">
              <input
                type="checkbox"
                checked={isSuperuser}
                onChange={(event) => handleSuperadminChange(event.target.checked)}
                disabled={role !== "admin"}
              />
              <span>System Superadmin</span>
            </label>
          </div>
          <p className="field-hint field-hint-inline">
            Superadmin is reserved for system-level account and access management. Only users with the admin role can hold it.
          </p>

          {error ? <p className="form-error">{error}</p> : null}
          {message ? <p className="form-success">{message}</p> : null}

          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating..." : "Create User"}
          </button>
        </form>
      </div>
    </div>
  );
}

function UserEditModal({
  user,
  departments,
  roles,
  onClose
}: {
  user: UserAdminItem;
  departments: DepartmentOption[];
  roles: RoleOption[];
  onClose: () => void;
}) {
  useModalBehavior(true, onClose);

  const router = useRouter();
  const [email, setEmail] = useState(user.email);
  const [fullName, setFullName] = useState(user.full_name || "");
  const [departmentId, setDepartmentId] = useState(user.department_id ? String(user.department_id) : "");
  const [role, setRole] = useState(user.roles[0] || "viewer");
  const [isActive, setIsActive] = useState(user.is_active);
  const [isSuperuser, setIsSuperuser] = useState(user.is_superuser);
  const [resetPassword, setResetPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isResetting, setIsResetting] = useState(false);

  function handleRoleChange(nextRole: string) {
    setRole(nextRole);
    if (nextRole !== "admin") {
      setIsSuperuser(false);
    }
  }

  function handleSuperadminChange(checked: boolean) {
    if (checked) {
      setRole("admin");
    }
    setIsSuperuser(checked);
  }

  async function saveUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsSaving(true);

    try {
      const response = await fetch(`/api/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          full_name: fullName || null,
          department_id: departmentId ? Number(departmentId) : null,
          is_active: isActive,
          is_superuser: isSuperuser,
          roles: [role]
        })
      });
      const payload = (await response.json()) as { detail?: string };
      if (!response.ok) {
        throw new Error(payload.detail || "Unable to update user");
      }
      setMessage("Updated.");
      router.refresh();
      // Optional: onClose() if we want to close immediately on success
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to update user");
    } finally {
      setIsSaving(false);
    }
  }

  async function resetUserPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setMessage(null);
    setIsResetting(true);

    try {
      const response = await fetch(`/api/users/${user.id}/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: resetPassword })
      });
      const payload = response.status === 204 ? null : ((await response.json()) as { detail?: string });
      if (!response.ok) {
        throw new Error(payload?.detail || "Unable to reset password");
      }
      setResetPassword("");
      setMessage("Password reset.");
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to reset password");
    } finally {
      setIsResetting(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h3>Edit User: {user.username}</h3>
            <p style={{ margin: "0.2rem 0 0", color: "var(--text-muted)", fontSize: "0.85rem" }}>
              Created: {user.created_at.slice(0, 10)}
            </p>
          </div>
          <button className="modal-close" onClick={onClose} aria-label="Close modal">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <form className="admin-user-form" onSubmit={saveUser}>
          <div className="admin-grid">
            <label>
              <span>Full Name</span>
              <input value={fullName} onChange={(event) => setFullName(event.target.value)} placeholder="Full name" />
            </label>
            <label>
              <span>Email</span>
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
            </label>
            <label>
              <span>Department</span>
              <select value={departmentId} onChange={(event) => setDepartmentId(event.target.value)}>
                <option value="">No department</option>
                {departments.map((department) => (
                  <option key={department.id} value={department.id}>{department.name}</option>
                ))}
              </select>
            </label>
            <label>
              <span>Role</span>
              <select value={role} onChange={(event) => handleRoleChange(event.target.value)}>
                {roles.map((item) => (
                  <option key={item.id} value={item.name}>{item.name}</option>
                ))}
              </select>
              <small className="field-hint">Role controls what the user can do inside the dashboard.</small>
            </label>
          </div>

          <div className="toggle-row">
            <label className="toggle">
              <input type="checkbox" checked={isActive} onChange={(event) => setIsActive(event.target.checked)} />
              <span>Active</span>
            </label>
            <label className="toggle">
              <input
                type="checkbox"
                checked={isSuperuser}
                onChange={(event) => handleSuperadminChange(event.target.checked)}
                disabled={role !== "admin"}
              />
              <span>System Superadmin</span>
            </label>
          </div>
          <p className="field-hint field-hint-inline">
            Superadmin is reserved for system-level account and access management. Only users with the admin role can hold it.
          </p>

          <button type="submit" disabled={isSaving}>
            {isSaving ? "Saving..." : "Save User"}
          </button>
        </form>

        <div className="admin-divider"></div>

        <form className="inline-form" onSubmit={resetUserPassword}>
          <label>
            <span>Reset Password</span>
            <input
              type="password"
              value={resetPassword}
              onChange={(event) => setResetPassword(event.target.value)}
              placeholder="New temporary password"
              minLength={8}
              required
            />
          </label>
          <button type="submit" disabled={isResetting}>
            {isResetting ? "Resetting..." : "Reset Password"}
          </button>
        </form>

        {(error || message) && (
          <div style={{ marginTop: "1rem" }}>
            {error ? <p className="form-error">{error}</p> : null}
            {message ? <p className="form-success">{message}</p> : null}
          </div>
        )}
      </div>
    </div>
  );
}

export function UserManagement({
  users,
  departments,
  roles
}: {
  users: UserAdminItem[];
  departments: DepartmentOption[];
  roles: RoleOption[];
}) {
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserAdminItem | null>(null);

  function getDepartmentName(depId: number | null) {
    if (!depId) return "N/A";
    const dep = departments.find(d => d.id === depId);
    return dep ? dep.name : "N/A";
  }

  return (
    <>
      {isCreateModalOpen && (
        <UserCreateModal
          departments={departments}
          roles={roles}
          onClose={() => setIsCreateModalOpen(false)}
        />
      )}

      {editingUser && (
        <UserEditModal
          user={editingUser}
          departments={departments}
          roles={roles}
          onClose={() => setEditingUser(null)}
        />
      )}

      <div className="panel stack">
        <div className="panel-header">
          <div>
            <h3>User Management</h3>
            <p>Create, edit and control access for user accounts.</p>
          </div>
          <button type="button" onClick={() => setIsCreateModalOpen(true)}>
            Create New User
          </button>
        </div>

        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr>
                <th>Username</th>
                <th>Full Name</th>
                <th>Department</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.id}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{user.username}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{user.email}</div>
                  </td>
                  <td>{user.full_name || "-"}</td>
                  <td>{getDepartmentName(user.department_id)}</td>
                  <td>
                    <span style={{ textTransform: "capitalize" }}>
                      {user.roles.join(", ") || "Viewer"}
                    </span>
                    {user.is_superuser && (
                      <span className="badge" style={{ marginLeft: "0.5rem", fontSize: "0.6rem" }}>Super Admin</span>
                    )}
                  </td>
                  <td>
                    <span className={`status-pill ${user.is_active ? "status-active" : "status-disconnected"}`}>
                      {user.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td>
                    <button className="table-action-btn" onClick={() => setEditingUser(user)}>
                      Edit
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
