import { redirect } from "next/navigation";

import { auth0 } from "@/lib/auth0";

export default async function LoginPage() {
  const session = await auth0.getSession();
  if (session) {
    redirect("/dashboard");
  }

  return (
    <main className="login-page">
      <h1>Todo</h1>
      <p>A simple todo list. Log in to see and manage your own tasks.</p>
      <a className="button" href="/auth/login">
        Log In
      </a>
    </main>
  );
}
