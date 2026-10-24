import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { expect, it } from 'vitest';
import { AccountManager } from './AccountManager';

it('shows the persisted work memo in my account as text, including untrusted markup', () => {
  const client = new QueryClient();
  client.setQueryData(['me'], { id: 'memo-customer', displayName: '고객', role: 'customer', provider: 'google', workMemo: '<b>내 작업 메모</b>' });
  client.setQueryData(['commerce', 'orders'], []);
  const html = renderToStaticMarkup(createElement(QueryClientProvider, { client }, createElement(AccountManager)));
  expect(html, 'my account must expose the work memo').toContain('작업 메모');
  expect(html).toContain('&lt;b&gt;내 작업 메모&lt;/b&gt;');
  expect(html).not.toContain('<b>내 작업 메모</b>');
});
