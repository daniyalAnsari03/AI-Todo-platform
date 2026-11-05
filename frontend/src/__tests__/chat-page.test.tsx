import { describe, it, expect, vi } from 'vitest';

vi.mock('next/navigation', () => ({
  redirect: vi.fn((url: string) => {
    throw new Error(`REDIRECT:${url}`);
  }),
}));

vi.mock('../lib/require-session', () => ({
  requireSession: vi.fn().mockResolvedValue({ user: { id: 'u1', name: 'Test' } }),
}));

import ChatPage from '../app/chat/page';

describe('Legacy chat route', () => {
  it('redirects to the dashboard', async () => {
    expect(() => ChatPage()).toThrow(/REDIRECT:\/dashboard/);
  });
});
