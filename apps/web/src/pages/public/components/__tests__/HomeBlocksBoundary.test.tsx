import React from 'react';
import { describe, it, expect, beforeEach, beforeAll, afterAll, vi } from 'vitest';
import type { MockInstance } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { HomeBlocksBoundary } from '../HomeBlocksBoundary';
import { HOME_FALLBACK_TITLE } from '../HomeUnavailable';
import { rumEvent } from '@shared/rum';
import { reportFeatureError } from '@shared/utils/sentry';
import { pushGlobalToast } from '@shared/ui/toastBus';

vi.mock('@shared/rum', () => ({
  rumEvent: vi.fn(),
}));
vi.mock('@shared/utils/sentry', () => ({
  reportFeatureError: vi.fn(),
}));
vi.mock('@shared/ui/toastBus', () => ({
  pushGlobalToast: vi.fn(),
}));

const mockedRumEvent = vi.mocked(rumEvent);
const mockedReportFeatureError = vi.mocked(reportFeatureError);
const mockedPushGlobalToast = vi.mocked(pushGlobalToast);

describe('HomeBlocksBoundary', () => {
  let consoleErrorSpy: MockInstance<[message?: any, ...optionalParams: any[]], void>;

  beforeAll(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  beforeEach(() => {
    mockedRumEvent.mockReset();
    mockedReportFeatureError.mockReset();
    mockedPushGlobalToast.mockReset();
  });

  it('пробрасывает дочерние элементы без ошибок', () => {
    render(
      <HomeBlocksBoundary slug="main" configVersion={1} etag="etag" resetKey="one">
        <span>ok</span>
      </HomeBlocksBoundary>,
    );

    expect(screen.getByText('ok')).toBeInTheDocument();
    expect(mockedRumEvent).not.toHaveBeenCalled();
    expect(mockedReportFeatureError).not.toHaveBeenCalled();
  });

  it('показывает fallback и репортит ошибку при падении дочернего компонента', () => {
    const Throwing = () => {
      throw new Error('block crashed');
    };

    render(
      <HomeBlocksBoundary slug="main" configVersion={42} etag="etag-42" resetKey="a" onRetry={vi.fn()}>
        <Throwing />
      </HomeBlocksBoundary>,
    );

    expect(screen.getByText(HOME_FALLBACK_TITLE)).toBeInTheDocument();
    expect(screen.getByText('block crashed')).toBeInTheDocument();
    expect(mockedReportFeatureError).toHaveBeenCalled();
    expect(mockedRumEvent).toHaveBeenCalledWith('home.render_error', expect.objectContaining({ slug: 'main', configVersion: 42 }));
    expect(mockedPushGlobalToast).toHaveBeenCalled();
  });

  it('вызывает onRetry при нажатии на кнопку «Обновить»', () => {
    const Throwing = () => {
      throw new Error('fail');
    };
    const onRetry = vi.fn();

    render(
      <HomeBlocksBoundary slug="main" configVersion={1} etag={null} resetKey="retry" onRetry={onRetry}>
        <Throwing />
      </HomeBlocksBoundary>,
    );

    const retryButton = screen.getByRole('button', { name: 'Обновить' });
    fireEvent.click(retryButton);

    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('сбрасывает состояние ошибки при смене resetKey', () => {
    function MaybeThrow({ shouldThrow }: { shouldThrow: boolean }) {
      if (shouldThrow) {
        throw new Error('boom');
      }
      return <span>ok</span>;
    }

    const { rerender } = render(
      <HomeBlocksBoundary slug="main" configVersion={1} etag={null} resetKey="first">
        <MaybeThrow shouldThrow />
      </HomeBlocksBoundary>,
    );

    expect(screen.getByText('boom')).toBeInTheDocument();

    rerender(
      <HomeBlocksBoundary slug="main" configVersion={1} etag={null} resetKey="second">
        <MaybeThrow shouldThrow={false} />
      </HomeBlocksBoundary>,
    );

    expect(screen.getByText('ok')).toBeInTheDocument();
  });
});

