import { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  showHeader?: boolean;
  className?: string;
}

export function Layout({ children, showHeader = true, className = '' }: LayoutProps) {
  return (
    <div className="min-h-screen bg-zinc-950 relative">
      {/* Ambient background effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Top gradient glow */}
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-amber-500/10 rounded-full blur-[120px]" />

        {/* Side accents */}
        <div className="absolute top-1/2 -left-20 w-[300px] h-[600px] bg-orange-500/5 rounded-full blur-[100px]" />
        <div className="absolute top-1/3 -right-20 w-[300px] h-[600px] bg-red-500/5 rounded-full blur-[100px]" />

        {/* Film grain overlay */}
        <div
          className="absolute inset-0 opacity-[0.015]"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
          }}
        />

        {/* Vignette effect */}
        <div
          className="absolute inset-0"
          style={{
            background: 'radial-gradient(ellipse at center, transparent 0%, rgba(0,0,0,0.4) 100%)',
          }}
        />
      </div>

      {showHeader && <Header />}

      <main className={`relative ${showHeader ? 'pt-16' : ''} ${className}`}>
        {children}
      </main>
    </div>
  );
}
