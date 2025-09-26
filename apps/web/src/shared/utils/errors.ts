
const DETAIL_MAP: Record<string, string> = {
  profile_not_found: 'Profile is not created yet. Fill in the form and save changes to create it.',
  invalid_avatar: 'Avatar link is invalid. Provide a valid URL or upload a file from your device.',
  avatar_too_long: 'Avatar link is too long. Please use a shorter URL.',
  invalid_email: 'Please enter a valid email address.',
  email_taken: 'This email is already in use.',
  email_rate_limited: 'Email was changed recently. Try again later.',
  token_invalid: 'The confirmation token is invalid or expired.',
};

function translateMessage(message: unknown): string | null {
  if (!message) return null;
  if (typeof message === 'string') {
    const trimmed = message.trim();
    return DETAIL_MAP[trimmed] || trimmed;
  }
  if (Array.isArray(message)) {
    const parts = message
      .map((item) => translateMessage(item))
      .filter((item): item is string => typeof item === 'string' && item.length > 0);
    return parts.length ? parts.join(', ') : null;
  }
  if (typeof message === 'object') {
    const detail = translateMessage((message as Record<string, unknown>).detail);
    if (detail) return detail;
    const error = translateMessage((message as Record<string, unknown>).error);
    if (error) return error;
    const msg = translateMessage((message as Record<string, unknown>).message);
    if (msg) return msg;
  }
  return null;
}

export function extractErrorMessage(err: unknown, fallback = 'Something went wrong'): string {
  if (err == null) return fallback;
  let raw: string | null = null;
  if (typeof err === 'string') raw = err;
  else if (err instanceof Error && typeof err.message === 'string') raw = err.message;
  else if (typeof (err as any)?.message === 'string') raw = String((err as any).message);
  else raw = String(err);

  const trimmed = raw?.trim() ?? '';
  if (!trimmed) return fallback;

  if (/^<!doctype/i.test(trimmed) || /^</.test(trimmed)) return fallback;
  const statusMatch = trimmed.match(/^HTTP\s(\d{3})/i);
  if (statusMatch) {
    const code = statusMatch[1];
    return `Request failed (HTTP ${code})`;
  }

  try {
    const parsed = JSON.parse(trimmed);
    const translated = translateMessage(parsed);
    if (translated) return translated;
  } catch {
    // not JSON, continue
  }

  if (/profile_not_found/i.test(trimmed)) return DETAIL_MAP.profile_not_found;
  if (/invalid_avatar/i.test(trimmed)) return DETAIL_MAP.invalid_avatar;
  if (/avatar_too_long/i.test(trimmed)) return DETAIL_MAP.avatar_too_long;
  if (/email_taken/i.test(trimmed)) return DETAIL_MAP.email_taken;
  if (/email_rate_limited/i.test(trimmed)) return DETAIL_MAP.email_rate_limited;

  return trimmed || fallback;
}
