import React from 'react';
import { Plane, ShieldCheck, Activity } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { SessionSelector } from './SessionSelector';

interface HeaderProps {
  currentSession: MockSession;
  onSelectSession: (session: MockSession) => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentSession,
  onSelectSession,
}) => {
  return (
    <header className="h-16 border-b border-slate-800/80 bg-dark-950/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-30 shadow-glass-sm">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded-xl bg-gradient-to-tr from-brand-blue to-brand-cyan text-white shadow-glow-blue">
          <Plane className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-bold text-base text-slate-100 tracking-tight">
              ParcelPilot
            </h1>
          </div>
          <p className="text-[11px] text-slate-400 font-sans hidden sm:block">
            AI B2B Logistics Support &amp; Policy Verification System
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <SessionSelector
          currentSession={currentSession}
          onSelectSession={onSelectSession}
        />
      </div>
    </header>
  );
};
