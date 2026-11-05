import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { Plus_Jakarta_Sans } from 'next/font/google';
import Script from 'next/script';

import './globals.css';

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-plus-jakarta-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Todo App',
  description: 'Premium task management for focused work.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <Script src="https://cdn.platform.openai.com/deployments/chatkit/chatkit.js" strategy="beforeInteractive" />
      </head>
      <body className={plusJakartaSans.variable}>{children}</body>
    </html>
  );
}
