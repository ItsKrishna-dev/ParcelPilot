import React from 'react';
import { UserRole } from '../../types/auth';
import { Sparkles, ArrowRight } from 'lucide-react';

interface PromptSuggestionsProps {
  role: UserRole;
  onSelectPrompt: (prompt: string) => void;
}

export const PromptSuggestions: React.FC<PromptSuggestionsProps> = ({
  role,
  onSelectPrompt,
}) => {
  const getSuggestions = () => {
    switch (role) {
      case 'customer':
        return [
          'Can I cancel ORD-1001 without a fee?',
          'Is ORD-2002 eligible for a service credit?',
          'Why is my shipment status delayed?',
          'What is my support response target?',
        ];
      case 'support_agent':
        return [
          'Investigate TKT-501',
          'Show tickets approaching SLA',
          'Explain KI-211',
          'Review the bulk-upload issue',
        ];
      case 'manager':
        return [
          'Review proactive support signals',
          'Inspect SLA risk',
          'Review unresolved product issues',
          'Show recent escalation activity',
        ];
    }
  };

  const suggestions = getSuggestions();

  return (
    <div className="my-4">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-400 mb-2">
        <Sparkles className="w-3.5 h-3.5 text-brand-blue" />
        <span>
          Suggested Prompts for{' '}
          {role === 'customer'
            ? 'Customer'
            : role === 'support_agent'
            ? 'Support Agent'
            : 'Manager'}
          :
        </span>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(prompt)}
            className="glass-panel p-3 rounded-lg border border-slate-800 text-left text-xs text-slate-300 hover:text-white hover:border-brand-blue/50 hover:bg-dark-800/80 transition-all flex items-center justify-between group"
          >
            <span className="line-clamp-2 pr-2">{prompt}</span>
            <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-brand-blue shrink-0 transition-transform group-hover:translate-x-0.5" />
          </button>
        ))}
      </div>
    </div>
  );
};
