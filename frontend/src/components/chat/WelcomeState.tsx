import React from 'react';
import { Shield, Sparkles, Lock, Cpu, ArrowRight } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { PromptSuggestions } from './PromptSuggestions';

interface WelcomeStateProps {
  session: MockSession;
  onSelectPrompt: (prompt: string) => void;
}

export const WelcomeState: React.FC<WelcomeStateProps> = ({
  session,
  onSelectPrompt,
}) => {
  return (
    <div className="max-w-3xl mx-auto py-8 px-4 text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-blue/10 border border-brand-blue/30 text-brand-blue text-xs font-semibold mb-4 shadow-glow-blue">
        <Shield className="w-3.5 h-3.5" />
        <span>ParcelPilot Trust Operations Console</span>
      </div>

      <h1 className="text-2xl sm:text-3xl font-bold text-slate-100 mb-3 tracking-tight">
        Deterministic AI Support &amp; Policy Verification
      </h1>

      <p className="text-sm text-slate-400 max-w-xl mx-auto mb-6 leading-relaxed">
        Active session:{' '}
        <strong className="text-slate-200">{session.name}</strong> ({session.role}
        {session.accountName ? ` • ${session.accountName}` : ''}). All answers are
        backed by signed contract precedence, deterministic calculations, and
        auditable tool execution.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left mb-6 text-xs">
        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="p-2 rounded-lg bg-blue-500/10 text-brand-blue w-fit mb-2">
            <Cpu className="w-4 h-4" />
          </div>
          <h4 className="font-semibold text-slate-200 mb-1">
            Deterministic Engine
          </h4>
          <p className="text-slate-400 leading-normal">
            Calculations for fees, credits, and SLAs run in pure Python domain tools.
          </p>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="p-2 rounded-lg bg-violet-500/10 text-violet-400 w-fit mb-2">
            <Shield className="w-4 h-4" />
          </div>
          <h4 className="font-semibold text-slate-200 mb-1">
            Contract Precedence
          </h4>
          <p className="text-slate-400 leading-normal">
            Signed enterprise agreements override standard SOP policy rules.
          </p>
        </div>

        <div className="glass-panel p-3.5 rounded-xl border border-slate-800">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 w-fit mb-2">
            <Lock className="w-4 h-4" />
          </div>
          <h4 className="font-semibold text-slate-200 mb-1">
            Tenant Isolation
          </h4>
          <p className="text-slate-400 leading-normal">
            Row-Level Security enforces strict multi-tenant customer data boundaries.
          </p>
        </div>
      </div>

      <div className="text-left">
        <PromptSuggestions
          role={session.role}
          onSelectPrompt={onSelectPrompt}
        />
      </div>
    </div>
  );
};
