import { describe, expect, it } from "vitest";
import { modules } from "./modules";

describe("módulos empresariales", () => {
  it("mantiene identificadores únicos y permisos explícitos", () => {
    const ids = modules.map((module) => module.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(modules.every((module) => module.table && module.permission)).toBe(true);
  });

  it("define columnas y campos editables para cada módulo", () => {
    expect(modules.every((module) => module.columns.length > 0)).toBe(true);
    expect(modules.every((module) => module.fields.length > 0)).toBe(true);
  });
});
