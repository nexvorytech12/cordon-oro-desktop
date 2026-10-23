/// <reference types="vite/client" />

interface Window {
  desktop: {
    getVersion(): Promise<string>;
    openExternal(url: string): Promise<void>;
    saveFile(request: {
      defaultPath: string;
      filters: Array<{ name: string; extensions: string[] }>;
      dataBase64: string;
    }): Promise<string | null>;
    checkForUpdates(): Promise<unknown>;
    downloadUpdate(): Promise<unknown>;
    installUpdate(): Promise<void>;
    onUpdateStatus(callback: (payload: { status: string; detail?: any }) => void): () => void;
  };
}
