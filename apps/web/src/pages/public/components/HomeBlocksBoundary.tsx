import React from 'react';
import { rumEvent } from '@shared/rum';
import { reportFeatureError } from '@shared/utils/sentry';
import { pushGlobalToast } from '@shared/ui/toastBus';
import { HomeUnavailable, HOME_FALLBACK_DEFAULT_MESSAGE } from './HomeUnavailable';

type HomeBlocksBoundaryProps = {
  children: React.ReactNode;
  slug: string;
  configVersion?: number | null;
  etag?: string | null;
  onRetry?: () => void;
  resetKey?: string | number;
};

type HomeBlocksBoundaryState = {
  hasError: boolean;
  errorMessage: string;
};

const TOAST_MESSAGE = 'Не удалось отобразить раздел главной. Попробуйте обновить страницу.';

class HomeBlocksBoundary extends React.Component<HomeBlocksBoundaryProps, HomeBlocksBoundaryState> {
  private reported = false;

  state: HomeBlocksBoundaryState = {
    hasError: false,
    errorMessage: HOME_FALLBACK_DEFAULT_MESSAGE,
  };

  static getDerivedStateFromError(error: Error): HomeBlocksBoundaryState {
    const message = typeof error?.message === 'string' && error.message.trim().length
      ? error.message.trim()
      : HOME_FALLBACK_DEFAULT_MESSAGE;
    return { hasError: true, errorMessage: message };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    if (!this.reported) {
      this.reported = true;
      const { slug, configVersion, etag } = this.props;
      reportFeatureError(error, 'home-blocks', {
        slug,
        configVersion,
        etag,
        componentStack: info?.componentStack,
      });
      rumEvent('home.render_error', {
        slug,
        configVersion,
        etag,
      });
      pushGlobalToast({ intent: 'error', description: TOAST_MESSAGE });
    }
  }

  componentDidUpdate(prevProps: HomeBlocksBoundaryProps) {
    if (prevProps.resetKey !== this.props.resetKey) {
      this.clearErrorState();
    }
  }

  private clearErrorState() {
    this.reported = false;
    this.setState({ hasError: false, errorMessage: HOME_FALLBACK_DEFAULT_MESSAGE });
  }

  private handleRetry = () => {
    this.clearErrorState();
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      return <HomeUnavailable message={this.state.errorMessage} onRetry={this.handleRetry} />;
    }

    return this.props.children as React.ReactElement;
  }
}

export { HomeBlocksBoundary };
