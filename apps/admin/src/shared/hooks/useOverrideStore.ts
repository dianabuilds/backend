import { useSyncExternalStore } from "react";

interface OverrideState {
  enabled: boolean;
  reason: string;
}

let state: OverrideState = { enabled: false, reason: "" };
const listeners = new Set<() => void>();

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function getSnapshot() {
  return state;
}

export function setOverrideState(patch: Partial<OverrideState>) {
  state = { ...state, ...patch };
  listeners.forEach((l) => l());
}

export function getOverrideState(): OverrideState {
  return state;
}

export function useOverrideStore(): OverrideState {
  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}

