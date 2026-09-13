import { currentUser } from "./api";

export interface UserProfile {
  email: string;
  display: string;
  initials: string;
}

export function userProfile(): UserProfile | null {
  if (typeof window === "undefined") return null;
  const u = currentUser();
  if (!u) return null;
  const at = u.email.indexOf("@");
  const name = at > 0 ? u.email.slice(0, at) : u.email;
  const clean = name.replace(/[^a-zA-Z0-9]/g, "");
  return {
    email: u.email,
    display: name,
    initials: (clean || name).slice(0, 3).toUpperCase(),
  };
}