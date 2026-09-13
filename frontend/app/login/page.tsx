"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { api, ApiError, setCurrentUser, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (mode === "register") {
        await api.register(email, password);
      }
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      setCurrentUser(email);
      router.push("/workflows");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100 p-4 text-slate-800">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 shadow-lg">
        <h1 className="mb-1 text-center text-2xl font-bold tracking-tight">Flow</h1>
        <p className="mb-6 text-center text-xs text-slate-400">
          Build the solution you need — workflows, automations and APIs.
        </p>

        <div className="mb-5 flex rounded-md border border-slate-200 bg-slate-50 p-0.5">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              onClick={() => {
                setMode(m);
                setError(null);
              }}
              className={`flex-1 rounded px-3 py-1.5 text-xs font-medium capitalize transition-colors ${
                mode === m ? "bg-cyan-600 text-white" : "text-slate-400 hover:text-slate-600"
              }`}
            >
              {m}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="flex flex-col gap-3">
          <label className="text-xs font-medium text-slate-400">Email</label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-cyan-500"
          />
          <label className="text-xs font-medium text-slate-400">Password</label>
          <input
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none focus:border-cyan-500"
          />
          {error ? (
            <div className="rounded-md bg-rose-50 px-3 py-2 text-xs text-rose-600">{error}</div>
          ) : null}
          <button
            type="submit"
            disabled={busy}
            className="mt-2 rounded-md bg-cyan-600 px-3 py-2 text-sm font-semibold text-white transition-colors hover:bg-cyan-500 disabled:opacity-50"
          >
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}