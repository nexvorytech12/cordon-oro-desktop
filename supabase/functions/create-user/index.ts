import { createClient } from "jsr:@supabase/supabase-js@2";

const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type" };

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const authorization = req.headers.get("Authorization");
    if (!authorization) throw new Error("Sesión requerida");
    const url = Deno.env.get("SUPABASE_URL")!;
    const anon = Deno.env.get("SUPABASE_ANON_KEY")!;
    const userClient = createClient(url, anon, { global: { headers: { Authorization: authorization } } });
    const { data: allowed, error: permissionError } = await userClient.rpc("has_permission", { requested: "users.manage" });
    if (permissionError || !allowed) return Response.json({ error: "No autorizado" }, { status: 403, headers: cors });

    const { email, password, full_name, role_id } = await req.json();
    if (!email || !password || !full_name || !role_id || password.length < 10) {
      return Response.json({ error: "Datos incompletos o contraseña menor a 10 caracteres" }, { status: 400, headers: cors });
    }
    const admin = createClient(url, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!);
    const { data, error } = await admin.auth.admin.createUser({ email, password, email_confirm: true, user_metadata: { full_name } });
    if (error) throw error;
    const { error: profileError } = await admin.from("profiles").update({ full_name, role_id, is_active: true }).eq("id", data.user.id);
    if (profileError) {
      await admin.auth.admin.deleteUser(data.user.id);
      throw profileError;
    }
    return Response.json({ id: data.user.id }, { status: 201, headers: { ...cors, "Content-Type": "application/json" } });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "Error inesperado" }, { status: 400, headers: { ...cors, "Content-Type": "application/json" } });
  }
});
