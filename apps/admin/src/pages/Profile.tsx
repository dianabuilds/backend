import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import PageLayout from "./_shared/PageLayout";

type MeResponse = {
  username: string | null;
  bio: string | null;
  avatar_url: string | null;
};

const isValidUrl = (s: string): boolean => {
  try {
    new URL(s);
    return true;
  } catch {
    return false;
  }
};

export default function Profile() {
  const { addToast } = useToast();
  const [tab, setTab] = useState<"profile" | "settings">("profile");
  const [username, setUsername] = useState("");
  const [bio, setBio] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [timezone, setTimezone] = useState("");
  const [locale, setLocale] = useState("");

  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<MeResponse>("/users/me")).data,
  });

  const { data: profileData } = useQuery({
    queryKey: ["profile"],
    queryFn: async () =>
      (await api.get<{ timezone: string | null; locale: string | null }>(
        "/users/me/profile",
      )).data,
  });

  useEffect(() => {
    if (me) {
      setUsername(me.username ?? "");
      setBio(me.bio ?? "");
      setAvatarUrl(me.avatar_url ?? "");
    }
  }, [me]);

  useEffect(() => {
    if (profileData) {
      setTimezone(profileData.timezone ?? "");
      setLocale(profileData.locale ?? "");
    }
  }, [profileData]);

  const saveProfile = async () => {
    const u = username.trim();
    const b = bio.trim();
    const a = avatarUrl.trim();
    if (!u) {
      addToast({ title: "Username is required", variant: "error" });
      return;
    }
    if (a && !isValidUrl(a)) {
      addToast({ title: "Invalid avatar URL", variant: "error" });
      return;
    }
    try {
      await api.patch("/users/me", {
        username: u,
        bio: b || null,
        avatar_url: a || null,
      });
      addToast({ title: "Profile saved", variant: "success" });
    } catch (e) {
      addToast({
        title: "Save failed",
        description: e instanceof Error ? e.message : String(e),
        variant: "error",
      });
    }
  };

  const saveSettings = async () => {
    await api.patch("/users/me/profile", {
      timezone: timezone || null,
      locale: locale || null,
    });
    addToast({ title: "Settings saved", variant: "success" });
  };

  return (
    <PageLayout title="Profile">
      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setTab("profile")}
          className={tab === "profile" ? "font-bold" : ""}
        >
          Profile
        </button>
        <button
          onClick={() => setTab("settings")}
          className={tab === "settings" ? "font-bold" : ""}
        >
          Settings
        </button>
      </div>
      {tab === "profile" && (
        <div className="max-w-sm flex flex-col gap-2">
          <label className="text-sm" htmlFor="username">
            Username
          </label>
          <input
            id="username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="bio">
            Bio
          </label>
          <textarea
            id="bio"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="avatar-url">
            Avatar URL
          </label>
          <input
            id="avatar-url"
            value={avatarUrl}
            onChange={(e) => setAvatarUrl(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <button
            onClick={saveProfile}
            className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
          >
            Save profile
          </button>
        </div>
      )}
      {tab === "settings" && (
        <div className="max-w-sm flex flex-col gap-2">
          <label className="text-sm" htmlFor="tz">
            Timezone
          </label>
          <input
            id="tz"
            value={timezone}
            onChange={(e) => setTimezone(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <label className="text-sm" htmlFor="locale">
            Locale
          </label>
          <input
            id="locale"
            value={locale}
            onChange={(e) => setLocale(e.target.value)}
            className="px-2 py-1 border rounded text-sm"
          />
          <button
            onClick={saveSettings}
            className="mt-2 self-start px-3 py-1 rounded bg-gray-800 text-white text-sm"
          >
            Save settings
          </button>
        </div>
      )}
    </PageLayout>
  );
}
