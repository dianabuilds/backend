export type SafeStorage = {
  getItem: (key: string) => string | null;
  setItem: (key: string, value: string) => void;
  removeItem: (key: string) => void;
  clear: () => void;
};

function createSafeStorage(getStorage: () => Storage | null): SafeStorage {
  return {
    getItem(key) {
      try {
        return getStorage()?.getItem(key) ?? null;
      } catch {
        return null;
      }
    },
    setItem(key, value) {
      try {
        getStorage()?.setItem(key, value);
      } catch {
        /* ignore */
      }
    },
    removeItem(key) {
      try {
        getStorage()?.removeItem(key);
      } catch {
        /* ignore */
      }
    },
    clear() {
      try {
        getStorage()?.clear();
      } catch {
        /* ignore */
      }
    },
  };
}

export const safeLocalStorage = createSafeStorage(() => {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
});

export const safeSessionStorage = createSafeStorage(() => {
  if (typeof window === "undefined") return null;
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
});
