import React from 'react';
import {
  MessageSquare,
  Package,
  Ticket,
  Shield,
  Clock,
  Layers,
  FileText,
  FileCheck,
  Lock,
  Sparkles,
} from 'lucide-react';
import { MockSession, UserRole } from '../../types/auth';
import { ActiveNavView } from '../../types/ui';
import { cn } from '../../lib/utils';

interface SidebarProps {
  session: MockSession;
  activeView: ActiveNavView;
  onSelectView: (view: ActiveNavView) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  session,
  activeView,
  onSelectView,
}) => {
  const role = session.role;

  const renderNavButton = (
    view: ActiveNavView,
    label: string,
    Icon: any,
    badge?: string
  ) => {
    const isActive = activeView === view;
    return (
      <button
        onClick={() => onSelectView(view)}
        className={cn(
          'w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all text-left mb-1',
          isActive
            ? 'bg-brand-blue/20 text-slate-100 border border-brand-blue/40 shadow-glow-blue'
            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
        )}
      >
        <div className="flex items-center gap-2.5">
          <Icon className={cn('w-4 h-4', isActive ? 'text-brand-blue' : 'text-slate-500')} />
          <span>{label}</span>
        </div>
        {badge && (
          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
            {badge}
          </span>
        )}
      </button>
    );
  };

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-dark-950/90 p-4 flex flex-col justify-between shrink-0 hidden md:flex h-full overflow-y-auto">
      <div className="space-y-6">
        {/* Active Context Banner */}
        <div className="glass-panel p-3 rounded-xl border border-slate-800 text-xs">
          <span className="text-[10px] uppercase font-mono text-slate-500 block mb-1">
            Active Role Context
          </span>
          <div className="font-semibold text-slate-200 flex items-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-brand-blue" />
            <span className="capitalize">{role.replace('_', ' ')}</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-1 truncate">
            {session.accountName || session.name}
          </p>
        </div>

        {/* Navigation Group */}
        <div>
          <span className="text-[10px] uppercase font-mono font-bold text-slate-500 px-3 block mb-2 tracking-wider">
            {role === 'customer' ? 'Customer Portal' : 'Operations Console'}
          </span>

          <nav>
            {role === 'customer' ? (
              <>
                {renderNavButton('chat', 'Support Chat', MessageSquare)}
                {renderNavButton('orders', 'My Orders', Package)}
                {renderNavButton('tickets', 'My Tickets', Ticket)}
                {renderNavButton('coverage', 'Account Coverage', Shield)}
              </>
            ) : (
              <>
                {renderNavButton('chat', 'Operations Chat', MessageSquare)}
                {renderNavButton('tickets', 'Ticket Queue', Ticket)}
                {renderNavButton('sla_risk', 'SLA Risk Dashboard', Clock)}
                {renderNavButton('issue_clusters', 'Issue Clusters', Layers)}
                {renderNavButton('orders', 'System Orders', Package)}
                {role === 'manager' && (
                  <>
                    <div className="border-t border-slate-800 my-2 pt-2" />
                    <span className="text-[10px] uppercase font-mono font-bold text-slate-500 px-3 block mb-2 tracking-wider">
                      Manager Governance
                    </span>
                    {renderNavButton('knowledge_admin', 'Knowledge Admin', FileCheck)}
                    {renderNavButton('audit', 'Audit Log', FileText)}
                  </>
                )}
              </>
            )}
          </nav>
        </div>
      </div>
    </aside>
  );
};
