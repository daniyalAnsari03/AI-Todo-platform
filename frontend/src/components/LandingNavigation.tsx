"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

function Brand() {
  return (
    <Link href="/" className="brand" aria-label="Todo home">
      <span className="brand-mark">T</span>
      <span>Todo</span>
    </Link>
  );
}

function NavigationLinks({
  isAuthenticated,
  onNavigate,
}: {
  isAuthenticated: boolean;
  onNavigate?: () => void;
}) {
  return (
    <>
      <Link href="/" onClick={onNavigate}>Home</Link>
      <Link href="#features" onClick={onNavigate}>Features</Link>
      <Link href="#about" onClick={onNavigate}>About</Link>
      {isAuthenticated ? (
        <Link href="/dashboard" className="nav-cta" onClick={onNavigate}>
          Dashboard
        </Link>
      ) : (
        <>
          <Link href="/login" onClick={onNavigate}>Login</Link>
          <Link href="/register" className="nav-cta" onClick={onNavigate}>
            Get Started
          </Link>
        </>
      )}
    </>
  );
}

export default function LandingNavigation({
  isAuthenticated,
}: {
  isAuthenticated: boolean;
}) {
  const [menuOpen, setMenuOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const hasOpened = useRef(false);

  useEffect(() => {
    if (!menuOpen) return;
    hasOpened.current = true;
    function onKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === "Escape") setMenuOpen(false);
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [menuOpen]);

  useEffect(() => {
    if (!menuOpen && hasOpened.current) triggerRef.current?.focus();
  }, [menuOpen]);

  return (
    <header className="topbar container">
      <Brand />
      <nav className="nav" aria-label="Main navigation">
        <NavigationLinks isAuthenticated={isAuthenticated} />
      </nav>
      <button
        ref={triggerRef}
        type="button"
        className="menu-toggle landing-menu-toggle"
        aria-label={menuOpen ? "Close main menu" : "Open main menu"}
        aria-expanded={menuOpen}
        aria-controls="mobile-main-menu"
        onClick={() => setMenuOpen((current) => !current)}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          {menuOpen ? (
            <path d="m6 6 12 12M18 6 6 18" />
          ) : (
            <path d="M4 7h16M4 12h16M4 17h16" />
          )}
        </svg>
      </button>
      <div
        className={`landing-menu-backdrop${menuOpen ? " is-open" : ""}`}
        aria-hidden="true"
        onClick={() => setMenuOpen(false)}
      />
      <nav
        id="mobile-main-menu"
        className={`mobile-main-menu${menuOpen ? " is-open" : ""}`}
        aria-label="Mobile main navigation"
        aria-hidden={!menuOpen}
        inert={!menuOpen}
      >
        <NavigationLinks
          isAuthenticated={isAuthenticated}
          onNavigate={() => setMenuOpen(false)}
        />
      </nav>
    </header>
  );
}
