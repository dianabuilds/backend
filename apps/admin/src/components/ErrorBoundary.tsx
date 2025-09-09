import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Здесь можно интегрировать Sentry/логирование
    // Помечаем параметры как использованные, чтобы избежать TS6133
    void error;
    void errorInfo;
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    if (typeof window !== 'undefined') {
      window.location.reload();
    }
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return <>{this.props.fallback}</>;
      return (
        <div className="p-6">
          <h1 className="text-2xl font-bold mb-2">Что-то пошло не так</h1>
          <p className="mb-4 text-sm text-gray-600 dark:text-gray-300">
            {this.state.error?.message || 'Непредвиденная ошибка интерфейса.'}
          </p>
          <button
            onClick={this.handleReload}
            className="px-3 py-1 rounded bg-gray-800 text-white dark:bg-gray-700"
          >
            Перезагрузить
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
