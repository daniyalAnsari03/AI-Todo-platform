import AskAIWidget from "../../components/AskAIWidget";
import DashboardSidebar from "../../components/DashboardSidebar";
import TodoList from "../../components/TodoList";
import { requireSession } from "../../lib/require-session";

export default async function DashboardPage() {
  const appSession = await requireSession();

  return (
    <main className="dashboard-shell">
      <DashboardSidebar userName={appSession.user.name} />
      <section className="dashboard-main">
        <header className="dashboard-header">
          <div>
            <span className="eyebrow">Welcome back</span>
            <h1>{appSession.user.name}</h1>
          </div>
        </header>

        <TodoList userId={appSession.user.id} />
      </section>
      <AskAIWidget userId={appSession.user.id} />
    </main>
  );
}
