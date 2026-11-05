'use client';

// Tasks T8105/T8109 — Spec FR-001–FR-003 and amendment; Plan §Design and Execution.
import { useEffect, useState } from 'react';
import { ChatKit, useChatKit } from '@openai/chatkit-react';
import { getToken, invalidateToken } from '../lib/token';

type ChatPanelProps = {
  userId: string;
  compact?: boolean;
  onShowHistoryReady?: (showHistory: () => Promise<void>) => void;
};

export default function ChatPanel({
  userId,
  compact = false,
  onShowHistoryReady,
}: ChatPanelProps) {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);
  const [tokenError, setTokenError] = useState(false);
  const [chatkitError, setChatkitError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const t = await getToken();
        if (mounted) setToken(t);
      } catch {
        if (mounted) setTokenError(true);
      } finally {
        if (mounted) setReady(true);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  const chatkitFetch = async (input: RequestInfo | URL, init?: RequestInit) => {
    let t = token || (await getToken());
    const headers = new Headers(init?.headers || {});
    headers.set('Authorization', `Bearer ${t || ''}`);
    let resp = await fetch(input, { ...init, headers });
    if (resp.status === 401) {
      invalidateToken();
      try {
        t = await getToken();
        const h2 = new Headers(init?.headers || {});
        h2.set('Authorization', `Bearer ${t || ''}`);
        resp = await fetch(input, { ...init, headers: h2 });
      } catch {
        window.location.assign('/login');
        throw new Error('Unauthorized');
      }
    }
    return resp;
  };

  const { control, showHistory } = useChatKit({
    api: {
      url: `/api/${userId}/chatkit`,
      domainKey: process.env.NEXT_PUBLIC_OPENAI_DOMAIN_KEY || 'local-dev',
      fetch: chatkitFetch,
    },
    composer: { attachments: { enabled: false } },
    theme: {
      colorScheme: 'dark',
      radius: 'round',
      color: { accent: { primary: '#7B4BD6', level: 2 } },
    },
    onError: ({ error }) => {
      setChatkitError(error.message || 'ChatKit encountered an error.');
    },
  });

  useEffect(() => {
    onShowHistoryReady?.(showHistory);
  }, [onShowHistoryReady, showHistory]);

  return (
    <>
      {tokenError || chatkitError ? (
        <div role="status" aria-live="polite">
          {tokenError && (
            <>
              Unable to load token. <a href="/login">Sign in again</a>.
            </>
          )}
          {tokenError && chatkitError ? ' ' : null}
          {chatkitError ? `ChatKit error: ${chatkitError}` : null}
        </div>
      ) : null}
      {ready && token && (
        <div
          className={`chatkit-frame${compact ? ' chatkit-frame-compact' : ''}`}
          style={{
            height: compact ? '100%' : '70vh',
            minHeight: compact ? 0 : 500,
            border: '1px solid currentColor',
          }}
        >
          <ChatKit
            control={control}
            style={{ height: '100%', width: '100%', display: 'block' }}
          />
        </div>
      )}
    </>
  );
}
