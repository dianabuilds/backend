import '@testing-library/jest-dom';

import { act, render, screen } from '@testing-library/react';

import { setWarningBanner } from '../shared/hooks';
import AdminOverrideBanner from './AdminOverrideBanner';

describe('AdminOverrideBanner', () => {
  afterEach(() => {
    act(() => {
      setWarningBanner(null);
    });
  });

  it('renders nothing when banner not set', () => {
    render(<AdminOverrideBanner />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('shows banner when set', () => {
    act(() => {
      setWarningBanner('Override active');
    });
    render(<AdminOverrideBanner />);
    expect(screen.getByText('Override active')).toBeInTheDocument();
  });
});
