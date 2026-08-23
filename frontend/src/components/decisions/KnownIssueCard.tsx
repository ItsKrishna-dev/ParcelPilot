import React from 'react';
import { AlertCircle, FileText, Wrench, CheckCircle2, ShieldAlert } from 'lucide-react';
import { Badge } from '../shared/Badge';
import { Card } from '../shared/Card';

interface KnownIssueCardProps {
  issueId: string;
  title: string;
  status?: string;
  guidance: string;
  sourceDoc?: string;
}

export const KnownIssueCard: React.FC<KnownIssueCardProps> = ({
  issueId,
  title,
  status = 'Verified Known Issue',
  guidance,
  sourceDoc = '04_Product_Operations_Guide_and_Known_Issues.pdf',
}) => {
  return (
    <Card className="border-l-4 border-l-amber-500 bg-amber-950/20 border-amber-500/30 my-3 space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertCircle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold text-amber-400">
                {issueId}
              </span>
              <h4 className="text-sm font-semibold text-slate-100">
                {title}
              </h4>
            </div>
            <span className="text-xs text-slate-400">
              Identified Product Operations Pattern
            </span>
          </div>
        </div>

        <Badge variant="amber" className="flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          {status}
        </Badge>
      </div>

      {/* Metadata Attributes Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 p-2.5 bg-dark-950/80 rounded-lg border border-amber-500/20 text-[11px] font-mono">
        <div>
          <span className="text-slate-500 block">Confidence</span>
          <span className="text-emerald-400 font-bold">95%</span>
        </div>
        <div>
          <span className="text-slate-500 block">Severity</span>
          <span className="text-amber-300 font-bold">Medium</span>
        </div>
        <div>
          <span className="text-slate-500 block">Verification</span>
          <span className="text-amber-300 font-bold">Recommended</span>
        </div>
        <div>
          <span className="text-slate-500 block">Escalation</span>
          <span className="text-emerald-400 font-bold">Not Required</span>
        </div>
      </div>

      {/* Workaround & Guidance */}
      <div className="bg-dark-950/70 p-3 rounded-lg border border-amber-500/20 text-xs text-slate-300">
        <div className="flex items-start gap-2">
          <Wrench className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <span className="font-medium text-amber-300 block mb-0.5">
              Workaround &amp; Recommended Next Step:
            </span>
            <p className="leading-relaxed text-slate-300">{guidance}</p>
          </div>
        </div>
      </div>

      {/* Source Doc */}
      <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
        <FileText className="w-3.5 h-3.5 text-slate-500" />
        <span>Source Document:</span>
        <span className="font-mono text-slate-300">{sourceDoc}</span>
      </div>
    </Card>
  );
};
