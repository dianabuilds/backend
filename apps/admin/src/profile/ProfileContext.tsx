/* eslint react-refresh/only-export-components: off */
import { createContext, type ReactNode, useCallback, useContext, useEffect, useState } from 'react';

import { api } from '../api/client';
import type { Account as Profile } from '../api/types';
import { safeLocalStorage } from '../utils/safeStorage';

function persistProfileId(id: string | null) {
  if (id) safeLocalStorage.setItem('profileId', id);
  else safeLocalStorage.removeItem('profileId');
}

interface ProfileContextType {
  profileId: string;
  setProfile: (profile: Profile | undefined) => void;
}

const ProfileContext = createContext<ProfileContextType>({
  profileId: '',
  setProfile: () => {},
});

function updateUrl(id: string) {
  try {
    const url = new URL(window.location.href);
    if (id) url.searchParams.set('profile_id', id);
    else url.searchParams.delete('profile_id');
    window.history.replaceState({}, '', url.pathname + url.search + url.hash);
  } catch {
    // ignore
  }
}

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profileId, setProfileIdState] = useState<string>(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const fromUrl = params.get('profile_id') || '';
      const stored = safeLocalStorage.getItem('profileId') || '';
      return fromUrl || stored;
    } catch {
      return '';
    }
  });

  const setProfile = useCallback((p: Profile | undefined) => {
    const id = p?.id ?? '';
    setProfileIdState(id);
    persistProfileId(id || null);
    updateUrl(id);
  }, []);

  useEffect(() => {
    persistProfileId(profileId || null);
    updateUrl(profileId);
  }, [profileId]);

  useEffect(() => {
    if (profileId) return;
    (async () => {
      try {
        // Backend may expose default_account_id for compatibility
        const me = await api.get<{ default_account_id: string | null }>('/users/me');
        const defId = me.data?.default_account_id;
        if (defId) {
          setProfileIdState(defId);
          persistProfileId(defId);
          updateUrl(defId);
          return;
        }
      } catch {
        // ignore
      }
      try {
        // Temporary compatibility: /profiles returns the expected set of profiles
        const res = await api.get<Profile[] | { accounts: Profile[] }>('/profiles');
        const payload = Array.isArray(res.data) ? res.data : res.data?.accounts || [];
        const global = payload.find(
          (it) => (it as { type?: string }).type === 'global' || it.slug === 'global',
        );
        if (global) {
          setProfileIdState(global.id);
          persistProfileId(global.id);
          updateUrl(global.id);
        }
      } catch {
        // ignore
      }
    })();
  }, [profileId]);

  return (
    <ProfileContext.Provider value={{ profileId, setProfile }}>{children}</ProfileContext.Provider>
  );
}

export function useProfile() {
  return useContext(ProfileContext);
}
