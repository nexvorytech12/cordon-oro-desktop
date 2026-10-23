import { app, BrowserWindow, dialog, ipcMain, shell } from "electron";
import updaterPackage from "electron-updater";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// electron-updater se publica como CommonJS. En Electron/Node ESM debe
// importarse el paquete predeterminado antes de extraer autoUpdater.
const { autoUpdater } = updaterPackage;
const currentDir = path.dirname(fileURLToPath(import.meta.url));
let mainWindow: BrowserWindow | null = null;

function sendUpdateStatus(status: string, detail?: unknown) {
  mainWindow?.webContents.send("updates:status", { status, detail });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 680,
    show: false,
    backgroundColor: "#F7F8FA",
    icon: app.isPackaged
      ? path.join(process.resourcesPath, "assets", "icon.ico")
      : path.join(currentDir, "..", "assets", "icon.ico"),
    title: "Cordón de Oro — Sistema de Gestión Empresarial",
    webPreferences: {
      preload: path.join(currentDir, "..", "electron", "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  mainWindow.removeMenu();
  mainWindow.once("ready-to-show", () => mainWindow?.show());
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith("https://")) void shell.openExternal(url);
    return { action: "deny" };
  });

  const devServer = process.env.VITE_DEV_SERVER_URL;
  if (devServer) void mainWindow.loadURL(devServer);
  else void mainWindow.loadFile(path.join(currentDir, "..", "dist", "index.html"));
}

app.setAppUserModelId("pe.cordondeoro.gestion");
const lock = app.requestSingleInstanceLock();
if (!lock) app.quit();
else {
  app.on("second-instance", () => {
    if (mainWindow?.isMinimized()) mainWindow.restore();
    mainWindow?.focus();
  });

  app.whenReady().then(() => {
    createWindow();
  });
}

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

autoUpdater.autoDownload = false;
autoUpdater.on("checking-for-update", () => sendUpdateStatus("checking"));
autoUpdater.on("update-available", (info) => sendUpdateStatus("available", info));
autoUpdater.on("update-not-available", (info) => sendUpdateStatus("current", info));
autoUpdater.on("download-progress", (progress) => sendUpdateStatus("downloading", progress));
autoUpdater.on("update-downloaded", (info) => sendUpdateStatus("downloaded", info));
autoUpdater.on("error", (error) => sendUpdateStatus("error", error.message));

ipcMain.handle("app:version", () => app.getVersion());
ipcMain.handle("app:open-external", async (_event, url: string) => {
  if (!/^https:\/\//i.test(url)) throw new Error("Solo se permiten enlaces HTTPS.");
  await shell.openExternal(url);
});
ipcMain.handle("file:save", async (_event, request: { defaultPath: string; filters: Electron.FileFilter[]; dataBase64: string }) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    defaultPath: request.defaultPath,
    filters: request.filters,
  });
  if (result.canceled || !result.filePath) return null;
  await writeFile(result.filePath, Buffer.from(request.dataBase64, "base64"));
  return result.filePath;
});
ipcMain.handle("updates:check", async () => {
  if (!app.isPackaged) return { development: true, version: app.getVersion() };
  const result = await autoUpdater.checkForUpdates();
  return result?.updateInfo ?? null;
});
ipcMain.handle("updates:download", () => autoUpdater.downloadUpdate());
ipcMain.handle("updates:install", () => autoUpdater.quitAndInstall(false, true));
