import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'PrecisionPulse - Real-time Telemetry Platform',
  description: 'Hybrid web-and-desktop ecosystem for real-time telemetry streaming',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
