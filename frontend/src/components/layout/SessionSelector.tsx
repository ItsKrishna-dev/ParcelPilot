import React from 'react';
import { UserCheck, Shield, ChevronDown } from 'lucide-react';
import { MockSession, MOCK_SESSIONS } from '../../types/auth';

interface SessionSelectorProps {
  currentSession: MockSession;
  onSelectSession: (session: MockSession) => void;
}

export const SessionSelector: React.FC<SessionSelectorProps> = ({
  currentSession,
  onSelectSession,
}) => {
  return (
    <div className="relative inline-block text-left">
      <div className="flex items-center gap-2 bg-dark-900 border border-slate-700/80 hover:border-brand-blue/50 rounded-xl px-3 py-1.5 transition-all shadow-sm">
        <div className="w-6 h-6 rounded-full bg-brand-blue/20 text-brand-blue border border-brand-blue/40 flex items-center justify-center font-bold text-xs">
          {currentSession.avatar}
        </div>
        <select
          value={currentSession.sessionId}
          onChange={(e) => {
            const found = MOCK_SESSIONS.find(
              (s) => s.sessionId === e.target.value
            );
            if (found) onSelectSession(found);
          }}
          className="bg-transparent text-xs font-semibold text-slate-100 focus:outline-none cursor-pointer pr-2"
        >
          <optgroup label="Customer Sessions">
            {MOCK_SESSIONS.filter((s) => s.role === 'customer').map((s) => (
              <option key={s.sessionId} value={s.sessionId} className="bg-dark-950 text-slate-200">
                {s.name} ({s.accountId})
              </option>
            ))}
          </optgroup>
          <optgroup label="Support Agent Sessions">
            {MOCK_SESSIONS.filter((s) => s.role === 'support_agent').map((s) => (
              <option key={s.sessionId} value={s.sessionId} className="bg-dark-950 text-slate-200">
                {s.name}
              </option>
            ))}
          </optgroup>
          <optgroup label="Manager Sessions">
            {MOCK_SESSIONS.filter((s) => s.role === 'manager').map((s) => (
              <option key={s.sessionId} value={s.sessionId} className="bg-dark-950 text-slate-200">
                {s.name}
              </option>
            ))}
          </optgroup>
        </select>
      </div>
    </div>
  );
};
