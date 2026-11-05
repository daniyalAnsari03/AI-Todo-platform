import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';

vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}));

vi.mock('../lib/require-session', () => ({
  requireSession: vi.fn().mockResolvedValue({ user: { id: 'u1', name: 'Test' } }),
}));

vi.mock('../components/TodoList', () => ({
  default: () => <div>TodoList</div>,
}));

import DashboardPage from '../app/dashboard/page';

describe('Dashboard', () => {
  it('offers Ask AI without a Chat sidebar link', async () => {
    const el: any = await DashboardPage();
    const { renderToString } = await import('react-dom/server');
    const html = renderToString(el);
    expect(html).toContain('Ask AI');
    expect(html).not.toContain('href="/chat"');
    expect(html).not.toContain('>Chat<');
  });
});
