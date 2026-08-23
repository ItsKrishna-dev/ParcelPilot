import React, { useState, useRef, useEffect } from 'react';
import { Send, RefreshCw, AlertCircle, Sparkles } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { ChatMessage } from '../../types/ui';
import { sendChatMessage } from '../../api/chat';
import { normalizeApiError } from '../../lib/errorUtils';
import { UserFacingError } from '../../types/trust';
import { WelcomeState } from './WelcomeState';
import { MessageCard } from './MessageCard';
import { Button } from '../shared/Button';

interface ChatContainerProps {
  session: MockSession;
}

export const ChatContainer: React.FC<ChatContainerProps> = ({ session }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState<UserFacingError | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-resize textarea logic
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(
        textareaRef.current.scrollHeight,
        140
      )}px`;
    }
  }, [input]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    const trimmedText = text.trim();

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: trimmedText,
      timestamp: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };

    setMessages((prev) => [...prev, userMessage]);
    // Clear input only if prompt chip was clicked; otherwise save draft in case of failure
    if (!textToSend) setInput('');
    setIsLoading(true);
    setApiError(null);

    try {
      const response = await sendChatMessage(trimmedText, session.sessionId);

      const agentMessage: ChatMessage = {
        id: `agent-${Date.now()}`,
        sender: 'agent',
        text: response.answer,
        timestamp: new Date().toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        response,
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (err: any) {
      const normalized = normalizeApiError(err);
      setApiError(normalized);
      // Restore input text if send failed
      if (!textToSend) {
        setInput(trimmedText);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const getPlaceholder = () => {
    switch (session.role) {
      case 'customer':
        return 'Ask about your orders, cancellations, credits, or shipment status…';
      case 'support_agent':
        return 'Ask about tickets, SLA status, order investigations, or policy guidelines…';
      case 'manager':
        return 'Review support signals, policy decisions, audit activity, or escalations…';
      default:
        return 'Ask about orders, cancellations, policy guidelines, or support tickets…';
    }
  };

  return (
    <div className="flex flex-col h-full max-w-5xl mx-auto px-4 py-4">
      <div className="flex-1 overflow-y-auto pr-1">
        {messages.length === 0 ? (
          <WelcomeState session={session} onSelectPrompt={(p) => handleSend(p)} />
        ) : (
          <div className="space-y-4 pb-4">
            {messages.map((msg) => (
              <MessageCard
                key={msg.id}
                message={msg}
                sessionId={session.sessionId}
              />
            ))}

            {/* Honest Loading Activity Indicator */}
            {isLoading && (
              <div className="flex justify-start my-4">
                <div className="flex items-center gap-3 glass-panel px-4 py-3 rounded-xl border border-brand-blue/30 text-xs text-brand-blue animate-pulse shadow-glow-blue">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Analyzing request and checking trusted sources…</span>
                </div>
              </div>
            )}

            {/* Normalized Error Banner */}
            {apiError && (
              <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center justify-between my-4">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
                  <div>
                    <strong className="block font-semibold text-red-300">
                      {apiError.title}
                    </strong>
                    <span>{apiError.message}</span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setApiError(null)}
                  className="text-red-300 hover:text-white"
                >
                  Dismiss
                </Button>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="pt-3 border-t border-slate-800/80">
        <div className="glass-panel rounded-xl p-2 border border-slate-800 focus-within:border-brand-blue/60 focus-within:ring-2 focus-within:ring-brand-blue/20 transition-all flex items-end gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={getPlaceholder()}
            disabled={isLoading}
            rows={1}
            className="flex-1 bg-transparent px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none resize-none min-h-[42px] max-h-36 overflow-y-auto leading-relaxed"
          />

          <Button
            variant="primary"
            size="md"
            onClick={() => handleSend()}
            disabled={!input.trim() || isLoading}
            isLoading={isLoading}
            className="shrink-0 mb-1"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </Button>
        </div>

        <div className="flex items-center justify-between text-[11px] text-slate-500 px-2 mt-1.5 font-mono">
          <span>
            Session: <strong className="text-slate-400">{session.sessionId}</strong>
          </span>
          <span>Press Enter to send • Shift+Enter for new line</span>
        </div>
      </div>
    </div>
  );
};
