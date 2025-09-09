interface OverrideState {
  enabled: boolean;
  reason: string;
}

let state: OverrideState = { enabled: false, reason: '' };

export function getOverrideState(): OverrideState {
  return state;
}
