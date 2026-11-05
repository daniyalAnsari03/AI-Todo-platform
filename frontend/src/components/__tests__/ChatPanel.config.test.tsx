// Task T8105 — Spec FR-001; Plan §Design and Execution, step 3.
import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import ChatPanel from '../ChatPanel';

const showHistoryMock = vi.fn().mockResolvedValue(undefined);
const useChatKitMock = vi.fn((options: Record<string, unknown>) => ({
  control: {},
  showHistory: showHistoryMock,
}));

vi.mock('@openai/chatkit-react', () => ({
  useChatKit: (options: Record<string, unknown>) => useChatKitMock(options),
  ChatKit: () => <div data-testid="chatkit">chat</div>,
}));

vi.mock('../../lib/token', () => ({
  getToken: vi.fn().mockResolvedValue('tok'),
  invalidateToken: vi.fn(),
}));

const { getToken, invalidateToken } = await import('../../lib/token');

describe('ChatPanel ChatKit options', () => {
  afterEach(() => {
    vi.clearAllMocks();
    (getToken as ReturnType<typeof vi.fn>).mockResolvedValue('tok');
    vi.unstubAllGlobals();
  });

  it('passes composer.attachments as an object, not a boolean', async () => {
    render(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');
    expect(useChatKitMock).toHaveBeenCalled();
    const options = useChatKitMock.mock.calls.at(-1)![0] as {
      composer?: { attachments?: unknown };
    };
    const attachments = options.composer?.attachments;
    expect(attachments).toEqual(expect.any(Object));
    expect(typeof attachments).not.toBe('boolean');
    expect(attachments).toMatchObject({ enabled: false });
  });

  it('points api.url at the per-user chatkit endpoint', async () => {
    render(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');
    const options = useChatKitMock.mock.calls.at(-1)![0] as {
      api?: { url?: string };
    };
    expect(options.api?.url).toBe('/api/user-123/chatkit');
  });

  it('uses only the supported dark ChatKit theme options', async () => {
    render(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');
    const options = useChatKitMock.mock.calls.at(-1)![0] as {
      theme?: {
        colorScheme?: string;
        radius?: string;
        color?: { accent?: { primary?: string; level?: number } };
      };
    };

    expect(options.theme).toEqual({
      colorScheme: 'dark',
      radius: 'round',
      color: { accent: { primary: '#7B4BD6', level: 2 } },
    });
  });

  it('exposes the supported history control to the sheet header', async () => {
    const onShowHistoryReady = vi.fn();
    render(
      <ChatPanel userId="user-123" onShowHistoryReady={onShowHistoryReady} />,
    );
    await screen.findByTestId('chatkit');

    await waitFor(() => {
      expect(onShowHistoryReady).toHaveBeenCalledWith(showHistoryMock);
    });
  });

  it('custom fetch attaches Authorization: Bearer', async () => {
    render(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');
    const options = useChatKitMock.mock.calls.at(-1)![0] as {
      api?: { fetch?: typeof fetch };
    };
    const fetchMock = vi.fn().mockResolvedValue(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    await options.api?.fetch?.('http://chatkit.test/api', {
      headers: { 'X-Custom': '1' },
    });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const call = fetchMock.mock.calls[0] as unknown as [
      unknown,
      { headers: Headers },
    ];
    const headers = new Headers(call[1].headers as unknown as HeadersInit);
    expect(headers.get('Authorization')).toBe('Bearer tok');
    expect(headers.get('X-Custom')).toBe('1');
  });

  it('refetches token and retries once on 401', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(new Response('{}', { status: 200 }));
    vi.stubGlobal('fetch', fetchMock);

    render(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');
    const options = useChatKitMock.mock.calls.at(-1)![0] as {
      api?: { fetch?: typeof fetch };
    };

    const resp = await options.api?.fetch?.('http://chatkit.test/api');

    expect(getToken).toHaveBeenCalledTimes(2);
    expect(invalidateToken).toHaveBeenCalledTimes(1);
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const secondCall = fetchMock.mock.calls[1] as unknown as [
      unknown,
      { headers: Headers },
    ];
    expect(new Headers(secondCall[1].headers as unknown as HeadersInit).get('Authorization')).toBe(
      'Bearer tok'
    );
    expect(resp?.status).toBe(200);
  });
});

describe('ChatPanel hook order regression', () => {
  it('renders loading -> chat without debug status or React hook-order errors', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { rerender } = render(<ChatPanel userId="user-123" />);
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByText(/user id:|token:/i)).not.toBeInTheDocument();

    rerender(<ChatPanel userId="user-123" />);
    await screen.findByTestId('chatkit');

    expect(screen.getByTestId('chatkit')).toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(errorSpy).not.toHaveBeenCalledWith(
      expect.stringMatching(/order of Hooks|Hooks .*order|Rendered more hooks/i)
    );

    errorSpy.mockRestore();
  });
});
