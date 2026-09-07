import { redirect } from "next/navigation";

import { auth0 } from "@/lib/auth0";
import TodoDashboard from "@/components/TodoDashboard";

export default async function DashboardPage() {
  const session = await auth0.getSession();
  if (!session) {
    redirect("/auth/login");
  }

  return (
    <main className="page">
      <div className="container">
        <TodoDashboard
          userName={session.user.name ?? session.user.email ?? "there"}
          userEmail={session.user.email ?? ""}
          userPicture={session.user.picture ?? undefined}
        />
      </div>
    </main>
  );
}
