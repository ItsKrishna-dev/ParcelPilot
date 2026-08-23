import React, { useState } from 'react';
import { MockSession, MOCK_SESSIONS } from './types/auth';
import { ActiveNavView } from './types/ui';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatContainer } from './components/chat/ChatContainer';
import { OrdersView } from './components/records/OrdersView';
import { TicketsView } from './components/records/TicketsView';
import { AccountCoverageView } from './components/records/AccountCoverageView';
import { InsightsDashboard } from './components/insights/InsightsDashboard';
import { KnowledgeAdminView } from './features/admin/KnowledgeAdminView';
import { AuditLogView } from './features/admin/AuditLogView';
import { MessageSquare, Package, Ticket, Shield, Activity, FileText } from 'lucide-react';

export function App() {
  const [currentSession, setCurrentSession] = useState<MockSession>(
    MOCK_SESSIONS[0]
  );
  const [activeView, setActiveView] = useState<ActiveNavView>('chat');

  const handleSelectSession = (newSession: MockSession) => {
    setCurrentSession(newSession);
    // If current activeView is not allowed in new role, reset to chat
    if (newSession.role !== 'manager' && (activeView === 'knowledge_admin' || activeView === 'audit')) {
      setActiveView('chat');
    } else if (newSession.role === 'customer' && (activeView === 'sla_risk' || activeView === 'issue_clusters')) {
      setActiveView('chat');
    }
  };

  const renderMainContent = () => {
    switch (activeView) {
      case 'chat':
        return <ChatContainer session={currentSession} />;
      case 'orders':
        return <OrdersView session={currentSession} />;
      case 'tickets':
        return <TicketsView session={currentSession} />;
      case 'coverage':
        return <AccountCoverageView session={currentSession} />;
      case 'sla_risk':
      case 'issue_clusters':
        return <InsightsDashboard session={currentSession} view={activeView} />;
      case 'knowledge_admin':
        return <KnowledgeAdminView session={currentSession} />;
      case 'audit':
        return <AuditLogView session={currentSession} />;
      default:
        return <ChatContainer session={currentSession} />;
    }
  };

  return (
    <div className="h-screen overflow-hidden bg-dark-950 text-slate-100 flex flex-col font-sans selection:bg-brand-blue/30 selection:text-white">
      <Header
        currentSession={currentSession}
        onSelectSession={handleSelectSession}
      />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          session={currentSession}
          activeView={activeView}
          onSelectView={setActiveView}
        />

        {/* Mobile Navigation Bar */}
        <div className="md:hidden flex items-center justify-around border-b border-slate-800 bg-dark-900 px-2 py-2 overflow-x-auto w-full sticky top-16 z-20">
          <button
            onClick={() => setActiveView('chat')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
              activeView === 'chat'
                ? 'bg-brand-blue text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            Chat
          </button>

          <button
            onClick={() => setActiveView('orders')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
              activeView === 'orders'
                ? 'bg-brand-blue text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Package className="w-3.5 h-3.5" />
            Orders
          </button>

          <button
            onClick={() => setActiveView('tickets')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
              activeView === 'tickets'
                ? 'bg-brand-blue text-white'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Ticket className="w-3.5 h-3.5" />
            Tickets
          </button>

          {currentSession.role === 'customer' ? (
            <button
              onClick={() => setActiveView('coverage')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
                activeView === 'coverage'
                  ? 'bg-brand-blue text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Shield className="w-3.5 h-3.5" />
              Coverage
            </button>
          ) : (
            <button
              onClick={() => setActiveView('sla_risk')}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 ${
                activeView === 'sla_risk' || activeView === 'issue_clusters'
                  ? 'bg-brand-blue text-white'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Insights
            </button>
          )}
        </div>

        <main className="flex-1 overflow-y-auto bg-dark-950/60 relative">
          {renderMainContent()}
        </main>
      </div>
    </div>
  );
}

export default App;
