"use client";

import { FileText, Workflow as WorkflowIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { userProfile, type UserProfile } from "@/lib/user";

export default function AppNav() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);

  useEffect(() => {
    setProfile(userProfile());
  }, []);

  return (
    <aside className="flex w-[52px] shrink-0 flex-col items-center border-r border-slate-200 bg-white py-2">
      <button
        title="Flow"
        onClick={() => router.push("/workflows")}
        className="mb-3 flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 shadow"
      >
        <span className="text-sm font-bold text-white">F</span>
      </button>

      <NavButton title="Home" onClick={() => router.push("/workflows")}>
        <WorkflowIcon className="h-[18px] w-[18px]" />
      </NavButton>
      <NavButton title="Workflows" onClick={() => router.push("/workflows")}>
        <FileText className="h-[18px] w-[18px]" />
      </NavButton>

      <div className="mt-auto">
        <span
          title={profile?.email ?? "Account"}
          className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 text-[10px] font-bold text-white"
        >
          {profile?.initials ?? "?"}
        </span>
      </div>
    </aside>
  );
}

function NavButton({
  title,
  onClick,
  children,
}: {
  title: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      title={title}
      onClick={onClick}
      className="mb-1 flex h-8 w-8 items-center justify-center rounded-lg text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-700"
    >
      {children}
    </button>
  );
}