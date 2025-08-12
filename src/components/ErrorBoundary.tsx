import React from 'react';
import { normalizeError } from '../errors/AppError';
import { logError } from '../telemetry';

type Props = {
  fallback?: React.ReactNode;
  onErrorCaptured?: (error: unknown) => void;
  children: React.ReactNode;
};

type State = {
  hasError: boolean;
  error?: unknown;
};

export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: unknown): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: unknown, errorInfo: React.ErrorInfo) {
    const appErr = normalizeError(error);
    logError(appErr, { componentStack: errorInfo.componentStack, scope: 'render' });
    this.props.onErrorCaptured?.(appErr);
  }

  handleReload = () => {
    // Простой сценарий восстановления
    if (typeof window !== 'undefined') window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return <>{this.props.fallback}</>;
      return (
        <div style={{ padding: 24 }}>
          <h2>Что-то пошло не так</h2>
          <p>Мы уже получили информацию об ошибке. Попробуйте обновить страницу.</p>
          <button onClick={this.handleReload} style={{ marginTop: 12 }}>Обновить</button>
        </div>
      );
    }
    return this.props.children as React.ReactElement;
  }
}
