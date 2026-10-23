import { createClient } from "@supabase/supabase-js";
import type { User } from "@supabase/supabase-js";
import type { Profile } from "../types";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

export const configurationReady = Boolean(url && anonKey);
export const supabase = createClient(url || "https://invalid.supabase.co", anonKey || "missing", {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: false,
  },
});

export async function loadProfile(user: User): Promise<Profile> {
  const { data, error } = await supabase
    .from("profiles")
    .select("full_name,is_active,roles(name,role_permissions(permissions(code)))")
    .eq("id", user.id)
    .single();
  if (error) throw error;
  if (!data?.is_active) throw new Error("La cuenta está desactivada. Contacte al administrador.");

  const roleValue = Array.isArray(data.roles) ? data.roles[0] : data.roles;
  const role = roleValue as any;
  const permissions = (role?.role_permissions ?? [])
    .map((item: any) => {
      const permission = Array.isArray(item.permissions) ? item.permissions[0] : item.permissions;
      return permission?.code;
    })
    .filter(Boolean);

  return {
    id: user.id,
    email: user.email ?? "",
    fullName: data.full_name || user.email || "Usuario",
    role: role?.name || "sin_rol",
    permissions,
  };
}

export function can(profile: Profile, permission: string) {
  return profile.role === "administrador" || profile.permissions.includes(permission);
}
