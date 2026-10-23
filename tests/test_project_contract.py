from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_no_service_role_in_desktop_sources():
    inspected = [ROOT / "main.py", *ROOT.glob("config/*.py"), *ROOT.glob("services/*.py"), *ROOT.glob("ui/*.py"), *ROOT.glob("views/*.py")]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in inspected).lower()
    assert "supabase_service_role_key" not in combined


def test_critical_rpc_migration_exists():
    sql = (ROOT / "migrations" / "003_transactional_functions.sql").read_text(encoding="utf-8")
    for function in ("register_stock_movement", "register_sale", "open_cash_register", "close_cash_register"):
        assert f"function public.{function}" in sql


def test_rls_enabled_for_core_tables():
    sql = (ROOT / "migrations" / "002_security_rls.sql").read_text(encoding="utf-8")
    assert "enable row level security" in sql.lower()
    assert "public.has_permission" in sql


def test_release_workflow_has_integrity_check():
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(encoding="utf-8")
    assert "Get-FileHash -Algorithm SHA256" in workflow
    updater = (ROOT / "services" / "update_service.py").read_text(encoding="utf-8")
    assert "digest.hexdigest().lower() != expected" in updater

