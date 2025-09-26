import React, { useMemo } from 'react';
import { Button, Card, Checkbox, Input, InputErrorMsg } from '@ui';
import { useAuth } from '../../shared/auth';
import { useNavigate } from 'react-router-dom';
import { ArrowRightIcon, ShieldCheckIcon, SparklesIcon } from '@heroicons/react/24/outline';

export default function LoginPage() {
  const { login, errorMessage } = useAuth();
  const nav = useNavigate();

  const [loginValue, setLoginValue] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [remember, setRemember] = React.useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const ok = await login({ login: loginValue, password, remember });
    if (ok) nav('/dashboard');
  };

  const apiBase = (import.meta as any).env.VITE_API_BASE as string | undefined;
  const info = useMemo(() => `${apiBase || ''} · Auth via /v1/auth/login`, [apiBase]);

  return (
    <main className="relative flex min-h-screen flex-col lg:flex-row">
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-primary-600/10 via-purple-500/5 to-sky-400/10" />
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_30%_20%,rgba(129,140,248,0.22),transparent_55%),radial-gradient(circle_at_80%_0%,rgba(236,72,153,0.18),transparent_45%)] blur-3xl" />

      <section className="flex flex-1 flex-col justify-between px-10 py-12 text-white lg:max-w-[40%] lg:px-16">
        <div className="space-y-6">
          <span className="inline-flex items-center gap-2 rounded-full bg-white/20 px-4 py-1 text-xs font-semibold uppercase tracking-[0.4em] text-white/80">
            <SparklesIcon className="size-4" /> Tailux
          </span>
          <h1 className="text-4xl font-semibold leading-tight text-white drop-shadow-lg">
            Welcome to the caves operations cockpit
          </h1>
          <p className="max-w-md text-sm text-white/80">
            Monitor worlds, orchestrate AI quests, and keep storytellers inspired across the entire network.
          </p>
        </div>
        <div className="space-y-4 text-sm text-white/70">
          <div className="inline-flex items-center gap-3 rounded-2xl bg-white/15 px-4 py-3 backdrop-blur-sm">
            <ShieldCheckIcon className="size-5" /> SOC2-ready security with hardware key support
          </div>
          <div className="flex flex-wrap gap-3 text-xs text-white/60">
            <span>24/7 observability</span>
            <span>Playbook automations</span>
            <span>Realtime quest drafting</span>
          </div>
        </div>
      </section>

      <section className="relative flex flex-1 items-center justify-center px-6 py-12 lg:px-16">
        <Card skin="bordered" className="w-full max-w-md border-white/30 bg-white/90 p-8 shadow-[0_35px_65px_-45px_rgba(79,70,229,0.65)] backdrop-blur-xl dark:bg-dark-800/90">
          <div className="space-y-2 text-center">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Sign in</h2>
            <p className="text-sm text-gray-500 dark:text-dark-200">Use your operator credentials to access control panels.</p>
          </div>

          <form onSubmit={onSubmit} autoComplete="off" className="mt-8 space-y-6">
            <Input
              label="Login"
              placeholder="Enter login or email"
              value={loginValue}
              onChange={(e) => setLoginValue(e.target.value)}
            />
            <Input
              label="Password"
              placeholder="Enter password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <InputErrorMsg when={!!errorMessage}>{errorMessage}</InputErrorMsg>

            <div className="flex items-center justify-between">
              <Checkbox label="Remember me" checked={remember} onChange={(e) => setRemember(e.currentTarget.checked)} />
              <button type="button" className="text-xs font-semibold text-primary-600 hover:text-primary-500" onClick={() => nav('/support/reset')}>Forgot password?</button>
            </div>

            <Button type="submit" className="w-full">
              Enter command center
              <ArrowRightIcon className="size-4" />
            </Button>
          </form>

          <div className="mt-6 space-y-2 text-center text-xs text-gray-500 dark:text-dark-200">
            <p>{info}</p>
            <p>Need access? Reach out in #ops-onboarding.</p>
          </div>
        </Card>
      </section>
    </main>
  );
}
