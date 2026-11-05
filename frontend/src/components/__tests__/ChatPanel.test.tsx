// Task T8107 — Spec amendment; Plan §Approved-Scope Amendment Plan.
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ChatPanel from '../ChatPanel';

vi.mock('../../lib/token', () => ({
  getToken: vi.fn().mockResolvedValue('tok'),
  invalidateToken: vi.fn(),
}));

vi.mock('@openai/chatkit-react', () => ({
  useChatKit: () => ({ control: {} }),
  ChatKit: (props: { style?: import('react').CSSProperties }) => (
    <div data-testid="chatkit" style={props.style}>
      chat
    </div>
  ),
}));

describe('ChatPanel', () => {
  it('renders', async () => {
    render(<ChatPanel userId="user-123" />);
    const el = await screen.findByTestId('chatkit');
    expect(el).toBeInTheDocument();
  });

  it('wraps ChatKit with a non-zero explicit height', async () => {
    render(<ChatPanel userId="user-123" />);
    const el = await screen.findByTestId('chatkit');
    expect(el).toHaveStyle({
      height: '100%',
      width: '100%',
      display: 'block',
    });
    const wrapper = el.parentElement;
    expect(wrapper?.style.height).toBe('70vh');
    expect(wrapper?.style.minHeight).toBe('500px');
    expect(wrapper?.style.borderWidth).toBe('1px');
  });
});
