import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, AlertCircle, Award } from 'lucide-react';
import { EvidenceItem } from '../../types/api';
import { Badge } from '../shared/Badge';
import { cn } from '../../lib/utils';

interface EvidenceCardProps {
  evidence: EvidenceItem;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const isAgreement = evidence.filename?.toLowerCase().includes('agreement');
  const isDeprecated =
    evidence.status?.toLowerCase().includes('deprecated') ||
    evidence.filename?.toLowerCase().includes('deprecated');

  return (
    <div
      className={cn(
        'rounded-lg border text-xs transition-all mb-2 overflow-hidden',
        isAgreement
          ? 'bg-violet-950/20 border-violet-500/30'
          : isDeprecated
          ? 'bg-slate-900/30 border-slate-800 opacity-70'
          : 'bg-dark-900/80 border-slate-800'
      )}
    >
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-3 flex items-center justify-between gap-3 cursor-pointer hover:bg-slate-800/40 select-none"
      >
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={cn(
              'p-1.5 rounded border shrink-0',
              isAgreement
                ? 'bg-violet-500/10 text-violet-400 border-violet-500/20'
                : isDeprecated
                ? 'bg-slate-800 text-slate-500 border-slate-700'
                : 'bg-blue-500/10 text-brand-blue border-blue-500/20'
            )}
          >
            {isAgreement ? (
              <Award className="w-4 h-4" />
            ) : (
              <FileText className="w-4 h-4" />
            )}
          </div>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-200 truncate">
                {evidence.filename}
              </span>
              {isAgreement && (
                <Badge variant="violet" size="sm" className="px-1.5 text-[10px]">
                  Signed Contract
                </Badge>
              )}
              {isDeprecated && (
                <Badge variant="slate" size="sm" className="px-1.5 text-[10px]">
                  Deprecated Policy
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
              <span>Doc ID: {evidence.doc_id}</span>
              {evidence.page && <span>Page {evidence.page}</span>}
              {evidence.score !== undefined && (
                <span>Relevance Score: {evidence.score}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-slate-400 shrink-0">
          <span className="text-[11px] text-slate-500 hidden sm:inline">
            {isExpanded ? 'Hide Excerpt' : 'View Excerpt'}
          </span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </div>
      </div>

      {isExpanded && (
        <div className="px-3 pb-3 pt-1 border-t border-slate-800/60 bg-dark-950/80">
          <p className="text-slate-300 font-mono text-[11px] leading-relaxed bg-slate-900/60 p-2.5 rounded border border-slate-800/60 whitespace-pre-wrap">
            {evidence.text}
          </p>
        </div>
      )}
    </div>
  );
};
