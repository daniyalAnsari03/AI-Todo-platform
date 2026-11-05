import Link from "next/link";
import LandingNavigation from "../components/LandingNavigation";
import { getSession } from "../lib/auth";

export default async function HomePage() {
  let isAuthenticated = false;
  try {
    isAuthenticated = (await getSession()) !== null;
  } catch {
    isAuthenticated = false;
  }

  return (
    <main className="landing-shell">
      <LandingNavigation isAuthenticated={isAuthenticated} />

      <section className="hero container">
        <div className="hero-copy">
          <span className="eyebrow">Everything in one focus flow</span>
          <h1>Your Tasks, Simplified.</h1>
          <p>
            Plan your day, track your progress, and stay organized with a calm,
            lightweight workflow designed for real life.
          </p>

          <div className="cta-row">
            {isAuthenticated ? (
              <Link href="/dashboard" className="button-primary large">
                Go to Dashboard
              </Link>
            ) : (
              <Link href="/register" className="button-primary large">
                Get Started Free
              </Link>
            )}
            <Link href="#features" className="button-secondary large">
              Learn More
            </Link>
          </div>

          <div className="mini-stats" aria-label="Key product stats">
            <div>
              <strong>10k+</strong>
              <span>Tasks cleared</span>
            </div>
            <div>
              <strong>2x</strong>
              <span>Faster planning</span>
            </div>
            <div>
              <strong>24/7</strong>
              <span>Focus support</span>
            </div>
          </div>
        </div>

        <div className="hero-visual" aria-label="Todo dashboard preview">
          <div className="preview-window">
            <div className="window-header">
              <span className="dot dot-green" />
              <span className="dot dot-gold" />
              <span className="dot dot-slate" />
            </div>

            <div className="preview-body">
              <aside className="preview-sidebar">
                <div className="sidebar-pill active">Today</div>
                <div className="sidebar-pill">Inbox</div>
                <div className="sidebar-pill">Upcoming</div>
              </aside>

              <div className="preview-main">
                <div className="preview-topline">
                  <span>Monday, 9:00 AM</span>
                  <span className="tag">3 tasks</span>
                </div>

                <div className="task-checklist">
                  <div className="task-item done">
                    <span className="check" />
                    <span>Review sprint notes</span>
                  </div>
                  <div className="task-item">
                    <span className="check" />
                    <span>Plan team sync</span>
                  </div>
                  <div className="task-item">
                    <span className="check" />
                    <span>Ship marketing draft</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="features container">
        <div className="section-heading">
          <span className="eyebrow">Features</span>
          <h2>Built for calm, focused work.</h2>
        </div>

        <div className="feature-grid">
          <article className="feature-card">
            <div className="icon-wrap" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="m5 12 4 4L19 6" />
              </svg>
            </div>
            <h3>Quick capture</h3>
            <p>Write down tasks in seconds and keep your workflow friction-free.</p>
          </article>
          <article className="feature-card">
            <div className="icon-wrap" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="8" />
                <circle cx="12" cy="12" r="3" />
              </svg>
            </div>
            <h3>Stay on track</h3>
            <p>Check progress at a glance with clear complete and pending states.</p>
          </article>
          <article className="feature-card">
            <div className="icon-wrap" aria-hidden="true">
              <svg viewBox="0 0 24 24">
                <path d="M20 7v5h-5M4 17v-5h5" />
                <path d="M6.5 9a6 6 0 0 1 10-2L20 12M4 12l3.5 5a6 6 0 0 0 10-2" />
              </svg>
            </div>
            <h3>Simple edits</h3>
            <p>Update details or revise your plan without losing momentum.</p>
          </article>
        </div>
      </section>

      <section id="about" className="about container">
        <div className="about-card">
          <div>
            <span className="eyebrow">About</span>
            <h2>More clarity, less clutter.</h2>
          </div>
          <p>
            Todo helps you keep priorities visible, work steadily, and finish the
            day with confidence. The experience is intentionally clean, minimal, and
            easy to return to anytime.
          </p>
        </div>
      </section>

      <footer className="site-footer">
        <div className="container footer-inner">
          <div>
            <Link href="/" className="brand">
              <span className="brand-mark">T</span>
              <span>Todo</span>
            </Link>
          </div>

          <div className="footer-links">
            <div>
              <h4>Quick links</h4>
              <Link href="/">Home</Link>
              <Link href="#features">Features</Link>
              <Link href="/dashboard">Dashboard</Link>
            </div>
            <div>
              <h4>Support</h4>
              <Link href="#about">Help center</Link>
              <Link href="#features">Contact</Link>
            </div>
          </div>
        </div>
        <div className="container footer-bottom">© 2026 Todo. All rights reserved.</div>
      </footer>
    </main>
  );
}