"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import { NotificationListResponse } from "@/lib/types";

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC"
  }).format(date);
}

export function NotificationBell() {
  const router = useRouter();
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [data, setData] = useState<NotificationListResponse>({ items: [], unread_count: 0 });

  async function loadNotifications() {
    setIsLoading(true);
    try {
      const response = await fetch("/api/notifications", { cache: "no-store" });
      const payload = (await response.json()) as NotificationListResponse | { detail?: string };
      if (response.ok) {
        setData(payload as NotificationListResponse);
      }
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadNotifications();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function handleReadAll() {
    await fetch("/api/notifications/read-all", { method: "POST" });
    await loadNotifications();
  }

  async function handleNotificationClick(notificationId: number, linkUrl: string | null) {
    await fetch(`/api/notifications/${notificationId}/read`, { method: "POST" });
    await loadNotifications();
    setIsOpen(false);
    if (linkUrl) {
      router.push(linkUrl);
      router.refresh();
    }
  }

  return (
    <div className="notification-container" ref={dropdownRef}>
      <button
        className="theme-toggle-btn notification-btn"
        onClick={() => setIsOpen((value) => !value)}
        aria-label="Notifications"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M15 17h5l-1.4-1.4A2 2 0 0 1 18 14.2V11a6 6 0 1 0-12 0v3.2a2 2 0 0 1-.6 1.4L4 17h5"></path>
          <path d="M9 17a3 3 0 0 0 6 0"></path>
        </svg>
        {data.unread_count > 0 ? <span className="notification-badge">{data.unread_count}</span> : null}
      </button>

      {isOpen ? (
        <div className="dropdown-menu notification-menu">
          <div className="dropdown-header notification-header">
            <div>
              <p className="dropdown-name">Notifications</p>
              <p className="dropdown-email">
                {data.unread_count > 0 ? `${data.unread_count} unread` : "No unread notifications"}
              </p>
            </div>
            <button className="dropdown-item notification-action" onClick={handleReadAll}>
              Read all
            </button>
          </div>

          <div className="notification-list">
            {isLoading ? (
              <div className="notification-empty">Loading notifications...</div>
            ) : data.items.length === 0 ? (
              <div className="notification-empty">No notifications yet.</div>
            ) : (
              data.items.map((item) => (
                <button
                  key={item.id}
                  className={`notification-item${item.is_read ? "" : " notification-item-unread"}`}
                  onClick={() => handleNotificationClick(item.id, item.link_url)}
                >
                  <div className="notification-item-top">
                    <strong>{item.title}</strong>
                    <span>{formatDate(item.created_at)}</span>
                  </div>
                  <p>{item.body}</p>
                </button>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
