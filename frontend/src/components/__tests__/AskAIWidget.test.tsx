import { fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

const historyMock = vi.hoisted(() => ({
  showHistory: vi.fn().mockResolvedValue(undefined),
}));

vi.mock('../ChatPanel', async () => {
  const React = await import('react');
  return {
    default: ({
      onShowHistoryReady,
    }: {
      onShowHistoryReady?: (showHistory: () => Promise<void>) => void;
    }) => {
      React.useEffect(() => {
        onShowHistoryReady?.(historyMock.showHistory);
      }, [onShowHistoryReady]);
      return <div data-testid="chat-panel">ChatKit conversation</div>;
    },
  };
});

import AskAIWidget from '../AskAIWidget';

describe('AskAIWidget', () => {
  it('opens an accessible right drawer and returns focus to the trigger when closed', async () => {
    const user = userEvent.setup();
    render(<AskAIWidget userId="u1" />);

    const trigger = screen.getByRole('button', { name: 'Ask AI' });
    const overlay = document.querySelector('.ask-ai-overlay');
    const backdrop = screen.getByTestId('ask-ai-backdrop');
    const drawer = document.querySelector('.ask-ai-drawer');

    expect(overlay).toHaveAttribute('data-state', 'closed');
    expect(backdrop).toHaveAttribute('data-state', 'closed');
    expect(backdrop).toHaveAttribute('aria-hidden', 'true');
    expect(drawer).toHaveAttribute('data-state', 'closed');
    expect(drawer).toHaveAttribute('aria-hidden', 'true');
    expect(drawer).toHaveAttribute('inert');
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await user.click(trigger);

    const dialog = screen.getByRole('dialog', { name: /ask ai/i });
    expect(overlay).toHaveAttribute('data-state', 'open');
    expect(backdrop).toHaveAttribute('data-state', 'open');
    expect(backdrop).toHaveAttribute('aria-hidden', 'false');
    expect(drawer).toHaveAttribute('data-state', 'open');
    expect(drawer).toHaveAttribute('aria-hidden', 'false');
    expect(drawer).not.toHaveAttribute('inert');
    expect(dialog).toHaveAttribute('aria-modal', 'true');
    expect(dialog).toHaveAttribute('data-side', 'right');
    expect(dialog.contains(document.activeElement)).toBe(true);
    expect(document.body).toHaveStyle({ overflow: 'hidden' });

    await user.keyboard('{Escape}');

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(overlay).toHaveAttribute('data-state', 'closed');
    expect(backdrop).toHaveAttribute('data-state', 'closed');
    expect(drawer).toHaveAttribute('data-state', 'closed');
    expect(trigger).toHaveFocus();
    expect(document.body).not.toHaveStyle({ overflow: 'hidden' });
  });

  it('closes from its close control and backdrop', async () => {
    const user = userEvent.setup();
    render(<AskAIWidget userId="u1" />);
    await user.click(screen.getByRole('button', { name: 'Ask AI' }));

    await user.click(screen.getByRole('button', { name: /close ask ai/i }));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: 'Ask AI' }));
    fireEvent.click(screen.getByTestId('ask-ai-backdrop'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(document.querySelector('.ask-ai-overlay')).toHaveAttribute(
      'data-state',
      'closed',
    );
  });

  it('keeps the existing ChatKit panel mounted across close and reopen', async () => {
    const user = userEvent.setup();
    render(<AskAIWidget userId="u1" />);

    await user.click(screen.getByRole('button', { name: 'Ask AI' }));
    const initialPanel = screen.getByTestId('chat-panel');
    const dialog = screen.getByRole('dialog', { name: /ask ai/i });
    const historyButton = within(dialog).getByRole('button', {
      name: /history/i,
    });
    await waitFor(() => expect(historyButton).toBeEnabled());
    await user.click(historyButton);
    expect(historyMock.showHistory).toHaveBeenCalledOnce();

    await user.keyboard('{Escape}');
    expect(screen.getByTestId('chat-panel')).toBe(initialPanel);

    await user.click(screen.getByRole('button', { name: 'Ask AI' }));
    expect(screen.getByTestId('chat-panel')).toBe(initialPanel);
  });

  it('closes from backdrop activation and traps focus inside the drawer', async () => {
    const user = userEvent.setup();
    render(<AskAIWidget userId="u1" />);

    await user.click(screen.getByRole('button', { name: 'Ask AI' }));
    const dialog = screen.getByRole('dialog', { name: /ask ai/i });
    const history = within(dialog).getByRole('button', {
      name: /show conversation history/i,
    });
    const close = within(dialog).getByRole('button', { name: /close ask ai/i });
    history.focus();
    await user.keyboard('{Shift>}{Tab}{/Shift}');
    expect(close).toHaveFocus();

    await user.keyboard('{Tab}');
    expect(history).toHaveFocus();

    fireEvent.click(screen.getByTestId('ask-ai-backdrop'));
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });
});
