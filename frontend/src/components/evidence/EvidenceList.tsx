import React from 'react';
import { EvidenceItem } from '../../types/api';
import { EvidenceCard } from './EvidenceCard';
import { BookOpen } from 'lucide-react';

interface EvidenceListProps {
  evidence: EvidenceItem[];
}

export const EvidenceList: React.FC<EvidenceListProps> = ({ evidence }) => {
  if (!evidence || evidence.length === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-slate-800/60">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-300 mb-2">
        <BookOpen className="w-3.5 h-3.5 text-brand-blue" />
        <span>Retrieved Evidence ({evidence.length} sources)</span>
      </div>

      <div className="space-y-1.5">
        {evidence.map((item, index) => (
          <EvidenceCard key={`${item.doc_id}-${index}`} evidence={item} />
        ))}
      </div>
    </div>
  );
};
