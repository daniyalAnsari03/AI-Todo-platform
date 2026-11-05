// Tasks T8102/T8107 — Spec FR-001–FR-003 and amendment; Plan §Design and Execution.
import { act, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const chatKitMocks = vi.hoisted(() => ({
  useChatKit: vi.fn((options: Record<string, unknown>) => {
    void options;
    return { control: {} };
  }),
}));

const tokenMocks = vi.hoisted(() => ({
  getToken: vi.fn(),
  invalidateToken: vi.fn(),
}));

vi.mock('../lib/token', () => tokenMocks);

vi.mock('@openai/chatkit-react', () => ({
  useChatKit: chatKitMocks.useChatKit,
  ChatKit: ({ style }: { style?: import('react').CSSProperties }) => (
    <div data-testid="chatkit" style={style}>
      chat
    </div>
  ),
}));

import ChatPanel from '../components/ChatPanel';

describe('ChatPanel status and ChatKit rendering', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    tokenMocks.getToken.mockResolvedValue('jwt-token-123');
    chatKitMocks.useChatKit.mockReturnValue({ control: {} });
  });

  it('renders ChatKit after token readiness without exposing the debug status', async () => {
    let resolveToken!: (token: string) => void;
    tokenMocks.getToken.mockReturnValue(
      new Promise<string>((resolve) => {
        resolveToken = resolve;
      }),
    );

    render(<ChatPanel userId="u1" />);

    expect(screen.queryByTestId('chatkit')).not.toBeInTheDocument();

    await act(async () => {
      resolveToken('jwt-token-123');
    });

    expect(await screen.findByTestId('chatkit')).toBeInTheDocument();
    expect(screen.queryByText(/user id:\s*present;\s*token:\s*ready/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
    expect(screen.queryByText('jwt-token-123')).not.toBeInTheDocument();
  });

  it('gives the visible ChatKit wrapper a concrete height and the host full-size styling', async () => {
    render(<ChatPanel userId="u1" />);

    const chatkit = await screen.findByTestId('chatkit');
    expect(chatkit).toHaveStyle({
      height: '100%',
      width: '100%',
      display: 'block',
    });

    const wrapper = chatkit.parentElement;
    expect(wrapper).not.toBeNull();
    expect(wrapper?.style.height).toBe('70vh');
    expect(wrapper?.style.minHeight).toBe('500px');
    expect(wrapper?.style.borderWidth).toBe('1px');
  });

  it('shows a visible token error without exposing a rejected token', async () => {
    tokenMocks.getToken.mockRejectedValue(new Error('private token failure'));

    render(<ChatPanel userId="u1" />);

    await waitFor(() => {
      expect(screen.getByRole('status')).toHaveTextContent(/unable to load/i);
    });
    expect(screen.getByRole('status')).not.toHaveTextContent(/user id:|token:/i);
    expect(screen.getByRole('status')).not.toHaveTextContent('private token failure');
    expect(screen.queryByText('Sign in required')).not.toBeInTheDocument();
  });

  it('shows ChatKit onError messages in the status line', async () => {
    render(<ChatPanel userId="u1" />);
    await screen.findByTestId('chatkit');

    const options = chatKitMocks.useChatKit.mock.calls.at(-1)?.[0] as {
      onError?: (event: { error: Error }) => void;
    };
    expect(options.onError).toBeTypeOf('function');

    act(() => {
      options.onError?.({ error: new Error('ChatKit connection failed') });
    });

    expect(screen.getByRole('status')).toHaveTextContent('ChatKit connection failed');
  });
});
