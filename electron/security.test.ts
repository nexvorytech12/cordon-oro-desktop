import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

describe("seguridad de Electron", () => {
  const main = readFileSync(resolve(process.cwd(), "electron/main.ts"), "utf8");

  it("aísla el renderer del proceso principal", () => {
    expect(main).toContain("contextIsolation: true");
    expect(main).toContain("nodeIntegration: false");
    expect(main).toContain("sandbox: true");
  });

  it("restringe enlaces externos a HTTPS", () => {
    expect(main).toContain('url.startsWith("https://")');
    expect(main).toContain("if (!/^https:\\/\\//i.test(url))");
  });

  it("carga electron-updater de forma compatible con CommonJS", () => {
    expect(main).toContain('import updaterPackage from "electron-updater"');
    expect(main).toContain("const { autoUpdater } = updaterPackage");
    expect(main).not.toContain('import { autoUpdater } from "electron-updater"');
  });
});
