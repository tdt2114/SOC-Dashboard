"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { AuthUser } from "@/lib/types";
import { useRouter } from "next/navigation";
export function UserDropdown({ currentUser }: { currentUser: AuthUser }) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  async function handleLogout() {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      router.push("/login");
      router.refresh();
    } catch (e) {
      console.error(e);
    }
  }

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="user-dropdown-container" ref={dropdownRef}>
      <button 
        className="user-avatar-btn" 
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Account menu"
      >
        <span className="avatar-initials">
          {currentUser.username.substring(0, 2).toUpperCase()}
        </span>
      </button>

      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-header">
            <p className="dropdown-name">{currentUser.full_name || currentUser.username}</p>
            <p className="dropdown-email">{currentUser.email}</p>
            <p className="dropdown-role">{currentUser.roles.join(", ")}</p>
          </div>
          <div className="dropdown-links">
            <Link href="/profile" className="dropdown-item" onClick={() => setIsOpen(false)}>
              Profile Settings
            </Link>
            <button className="dropdown-item dropdown-logout" onClick={handleLogout}>
              Sign Out
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
