import { describe, expect, it } from 'vitest';
import { extractErrorMessage } from './errors';

describe('extractErrorMessage', () => {
  it('translates known codes', () => {
    expect(extractErrorMessage('profile_not_found')).toBe(
      'Profile is not created yet. Fill in the form and save changes to create it.',
    );
  });

  it('parses json payloads with errors array', () => {
    const payload = JSON.stringify({ errors: [{ message: 'Invalid credentials' }] });
    expect(extractErrorMessage(payload, 'Fallback')).toBe('Invalid credentials');
  });

  it('flattens nested detail collections', () => {
    const message = extractErrorMessage({ detail: ['First issue', { message: 'Second issue' }] });
    expect(message).toBe('First issue, Second issue');
  });

  it('falls back when message empty', () => {
    expect(extractErrorMessage({ message: ' ' }, 'Fallback message')).toBe('Fallback message');
  });

  it('ignores HTML payloads', () => {
    expect(extractErrorMessage('<html><body>Error</body></html>', 'Oops')).toBe('Oops');
  });
});
