'use client';

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from 'react';

import ChatPanel from './ChatPanel';

type AskAIWidgetProps = {
  userId: string;
};

export default function AskAIWidget({ userId }: AskAIWidgetProps) {
  const [open, setOpen] = useState(false);
  const [hasOpened, setHasOpened] = useState(false);
  const [historyReady, setHistoryReady] = useState(false);
  const [historyError, setHistoryError] = useState('');
  const triggerRef = useRef<HTMLButtonElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const dialogRef = useRef<HTMLElement>(null);
  const showHistoryRef = useRef<(() => Promise<void>) | null>(null);

  const handleHistoryReady = useCallback((showHistory: () => Promise<void>) => {
    showHistoryRef.current = showHistory;
    setHistoryReady(true);
  }, []);

  useEffect(() => {
    if (open) {
      closeRef.current?.focus();
    } else if (hasOpened) {
      triggerRef.current?.focus();
    }
  }, [hasOpened, open]);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  useEffect(() => {
    if (!open) return;
    function onKeyDown(event: globalThis.KeyboardEvent) {
      if (event.key === 'Escape') {
        event.stopPropagation();
        setOpen(false);
      }
    }
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open]);

  function openSheet() {
    setHasOpened(true);
    setHistoryError('');
    setOpen(true);
  }

  async function openHistory() {
    try {
      await showHistoryRef.current?.();
      setHistoryError('');
    } catch (error) {
      setHistoryError(
        error instanceof Error ? error.message : 'Unable to open conversation history.',
      );
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape' && open) {
      event.stopPropagation();
      setOpen(false);
      return;
    }

    if (event.key === 'Tab' && open) {
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], input:not([disabled]), textarea:not([disabled]), openai-chatkit',
      );
      if (!focusable?.length) {
        event.preventDefault();
        return;
      }

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="ask-ai-trigger"
        aria-label="Ask AI"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={openSheet}
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M12 3.5 13.7 9l5.1 2-5.1 2L12 18.5 10.3 13l-5.1-2 5.1-2L12 3.5Z" />
          <path d="m19 15 .9 2.5 2.1.8-2.1.8L19 21.5l-.9-2.4-2.1-.8 2.1-.8L19 15Z" />
        </svg>
      </button>

      <div
        className="ask-ai-overlay"
        data-state={open ? 'open' : 'closed'}
        aria-hidden={!open}
        inert={!open}
        onKeyDown={handleKeyDown}
      >
          <div
            className="ask-ai-backdrop"
            data-testid="ask-ai-backdrop"
            data-state={open ? 'open' : 'closed'}
            aria-hidden={!open}
            onClick={(event) => {
              if (event.target === event.currentTarget) {
                setOpen(false);
              }
            }}
          />
          <section
            ref={dialogRef}
            className="ask-ai-drawer"
            role="dialog"
            aria-modal={open || undefined}
            aria-labelledby="ask-ai-title"
            data-side="right"
            data-state={open ? 'open' : 'closed'}
            aria-hidden={!open}
            inert={!open}
          >
            <header className="ask-ai-header">
              <span className="ask-ai-orb" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M12 3.5 13.7 9l5.1 2-5.1 2L12 18.5 10.3 13l-5.1-2 5.1-2L12 3.5Z" />
                </svg>
              </span>
              <h2 id="ask-ai-title">Ask AI</h2>
              <button
                type="button"
                className="ask-ai-icon-button"
                aria-label="Show conversation history"
                disabled={!historyReady}
                onClick={() => void openHistory()}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M4 5h16v14H4z" />
                  <path d="M8 9h8M8 13h8M8 17h4" />
                </svg>
              </button>
              <button
                ref={closeRef}
                type="button"
                className="ask-ai-icon-button"
                aria-label="Close Ask AI"
                onClick={() => setOpen(false)}
              >
                <svg viewBox="0 0 24 24" aria-hidden="true">
                  <path d="m6 6 12 12M18 6 6 18" />
                </svg>
              </button>
            </header>
            {historyError ? (
              <p className="ask-ai-error" role="alert">
                {historyError}
              </p>
            ) : null}
            <div className="ask-ai-chat">
              {hasOpened ? (
                <ChatPanel
                  userId={userId}
                  compact
                  onShowHistoryReady={handleHistoryReady}
                />
              ) : null}
            </div>
          </section>
      </div>
    </>
  );
}
