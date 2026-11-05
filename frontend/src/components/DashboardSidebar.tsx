"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type KeyboardEvent } from "react";

function Brand() {
  return (
    <Link href="/" className="brand" aria-label="Todo home">
      <span className="brand-mark">T</span>
      <span>Todo</span>
    </Link>
  );
}

function UserChip({ userName }: { userName: string }) {
  return (
    <div className="sidebar-user" aria-label={`Signed in as ${userName}`}>
      <span className="sidebar-avatar" aria-hidden="true">
        {userName.slice(0, 1).toUpperCase()}
      </span>
      <span>{userName}</span>
    </div>
  );
}

function NavigationLinks({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav className="sidebar-nav" aria-label="Dashboard navigation">
      <Link href="/dashboard" className="sidebar-link active" onClick={onNavigate}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M4 13h6V4H4zM14 20h6v-9h-6zM14 4h6v3h-6zM4 20h6v-3H4z" />
        </svg>
        Overview
      </Link>
      <Link href="/" className="sidebar-link" onClick={onNavigate}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-6v-7h-4v7H4a1 1 0 0 1-1-1z" />
        </svg>
        Home
      </Link>
      <Link href="/logout" className="sidebar-link" onClick={onNavigate}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M10 17l5-5-5-5M15 12H3" />
          <path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7" />
        </svg>
        Log out
      </Link>
    </nav>
  );
}

export default function DashboardSidebar({ userName }: { userName: string }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  const hasOpened = useRef(false);

  useEffect(() => {
    if (menuOpen) {
      hasOpened.current = true;
      drawerRef.current?.querySelector<HTMLElement>("a[href]")?.focus();
      const previousOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
      return () => {
        document.body.style.overflow = previousOverflow;
      };
    }
    if (hasOpened.current) triggerRef.current?.focus();
  }, [menuOpen]);

  useEffect(() => {
    if (!menuOpen) return;
    function onKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  function trapFocus(event: KeyboardEvent<HTMLElement>) {
    if (event.key !== "Tab") return;
    const focusable = drawerRef.current?.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled])',
    );
    if (!focusable?.length) {
      event.preventDefault();
      return;
    }
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return (
    <div className="dashboard-navigation">
      <header className="mobile-dashboard-bar">
        <Brand />
        <button
          ref={triggerRef}
          type="button"
          className="menu-toggle"
          aria-label="Open dashboard menu"
          aria-expanded={menuOpen}
          aria-controls="mobile-dashboard-menu"
          onClick={() => setMenuOpen(true)}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7h16M4 12h16M4 17h16" />
          </svg>
        </button>
      </header>

      <aside className="sidebar-panel" aria-label="Sidebar navigation">
        <div className="brand-block">
          <Brand />
        </div>
        <NavigationLinks />
        <UserChip userName={userName} />
      </aside>

      <div
        className={`mobile-menu-backdrop${menuOpen ? " is-open" : ""}`}
        aria-hidden="true"
        onClick={() => setMenuOpen(false)}
      />
      <aside
        ref={drawerRef}
        id="mobile-dashboard-menu"
        className={`mobile-sidebar${menuOpen ? " is-open" : ""}`}
        role={menuOpen ? "dialog" : undefined}
        aria-label="Dashboard menu"
        aria-modal={menuOpen || undefined}
        aria-hidden={!menuOpen}
        inert={!menuOpen}
        onKeyDown={trapFocus}
      >
        <div className="brand-block">
          <Brand />
          <button
            type="button"
            className="menu-close"
            aria-label="Close dashboard menu"
            onClick={() => setMenuOpen(false)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="m6 6 12 12M18 6 6 18" />
            </svg>
          </button>
        </div>
        <NavigationLinks onNavigate={() => setMenuOpen(false)} />
        <UserChip userName={userName} />
      </aside>
    </div>
  );
}
