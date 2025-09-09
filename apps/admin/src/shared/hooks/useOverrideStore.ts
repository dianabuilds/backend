interface OverrideState {
  enabled: boolean;
  reason: string;
}

const state: OverrideState = { enabled: false, reason: '' };

export function getOverrideState(): OverrideState {
  return state;
}
