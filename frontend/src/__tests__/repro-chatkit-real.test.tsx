// Temporary reproduction: real @openai/chatkit-react, no library mocks.
import { render } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

vi.mock('../lib/token', () => ({
  getToken: vi.fn().mockResolvedValue('tok'),
  invalidateToken: vi.fn(),
}));

import ChatPanel from '../components/ChatPanel';

describe('REAL chatkit-react repro', () => {
  it('mounts openai-chatkit and applies options', async () => {
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});

    const { container } = render(<ChatPanel userId="user-123" />);

    await new Promise((r) => setTimeout(r, 300));

    console.log('CONTAINER_HTML=' + (container.firstElementChild?.outerHTML ?? 'EMPTY_ROOT'));
    console.log('BODY_SNIPPET=' + document.body.innerHTML.slice(0, 500));

    console.log('ELEMENT_PRESENT', true);
    console.log('ELEMENT_DEFINED', Boolean(window.customElements?.get?.('openai-chatkit')));
    console.log('HAS_ERROR_SPY_CALLS', errorSpy.mock.calls.length);
    for (const c of errorSpy.mock.calls) console.log('ERR:', c.map(String).join(' | '));
    for (const c of warnSpy.mock.calls) console.log('WARN:', c.map(String).join(' | '));

    errorSpy.mockRestore();
    warnSpy.mockRestore();
  });
});
