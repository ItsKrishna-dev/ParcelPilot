import React, { useState } from 'react';
import { Terminal, ChevronDown, ChevronUp, Clock, FileCheck } from 'lucide-react';
import { ToolTraceEntry, EvidenceItem } from '../../types/api';
import { ToolTraceItem } from './ToolTraceItem';
import { EvidenceList } from '../evidence/EvidenceList';
import { formatMs } from '../../lib/utils';

interface ToolTraceDrawerProps {
  toolTrace: ToolTraceEntry[];
  evidence: EvidenceItem[];
}

export const ToolTraceDrawer: React.FC<ToolTraceDrawerProps> = ({
  toolTrace,
  evidence,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const totalLatency = toolTrace.reduce((acc, t) => acc + t.latency_ms, 0);
  const toolCount = toolTrace.length;

  if (toolCount === 0 && evidence.length === 0) return null;

  return (
    <div className="mt-4 border border-slate-800/80 rounded-xl overflow-hidden glass-panel">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="p-3 bg-dark-900/60 hover:bg-dark-850 flex items-center justify-between cursor-pointer select-none transition-colors"
      >
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-blue-500/10 text-brand-blue border border-blue-500/20">
            <Terminal className="w-4 h-4" />
          </div>
          <span className="text-xs font-semibold text-slate-200">
            Evidence &amp; Tool Trace
          </span>
          <div className="flex items-center gap-1.5 ml-2">
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] font-mono text-slate-300 border border-slate-700">
              {toolCount} {toolCount === 1 ? 'tool call' : 'tool calls'}
            </span>
            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-[10px] font-mono text-slate-300 border border-slate-700">
              {evidence.length} {evidence.length === 1 ? 'doc chunk' : 'doc chunks'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1 text-[11px] font-mono text-slate-400">
            <Clock className="w-3.5 h-3.5 text-slate-500" />
            <span>{formatMs(totalLatency)} total</span>
          </div>
          {isOpen ? (
            <ChevronUp className="w-4 h-4 text-slate-400" />
          ) : (
            <ChevronDown className="w-4 h-4 text-slate-400" />
          )}
        </div>
      </div>

      {isOpen && (
        <div className="p-4 border-t border-slate-800/60 space-y-3 bg-dark-950/90">
          {toolTrace.length > 0 && (
            <div>
              <h5 className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Tool Execution Pipeline
              </h5>
              {toolTrace.map((trace, idx) => (
                <ToolTraceItem key={`${trace.tool_name}-${idx}`} trace={trace} />
              ))}
            </div>
          )}

          {evidence.length > 0 && <EvidenceList evidence={evidence} />}
        </div>
      )}
    </div>
  );
};
