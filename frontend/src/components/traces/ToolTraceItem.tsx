import React, { useState } from 'react';
import { Wrench, ChevronDown, ChevronUp, Clock, CheckCircle, AlertTriangle, Lock } from 'lucide-react';
import { ToolTraceEntry } from '../../types/api';
import { Badge } from '../shared/Badge';
import { formatMs } from '../../lib/utils';

interface ToolTraceItemProps {
  trace: ToolTraceEntry;
}

export const ToolTraceItem: React.FC<ToolTraceItemProps> = ({ trace }) => {
  const [showRaw, setShowRaw] = useState(false);

  const status = trace.output?.status || 'OK';
  const getStatusBadge = () => {
    switch (status) {
      case 'OK':
        return <Badge variant="emerald">OK</Badge>;
      case 'NEEDS_VERIFICATION':
        return <Badge variant="amber">Needs Verification</Badge>;
      case 'ACCESS_DENIED':
        return <Badge variant="red">Access Denied</Badge>;
      case 'OUT_OF_SCOPE':
        return <Badge variant="slate">Out of Scope</Badge>;
      default:
        return <Badge variant="blue">{status}</Badge>;
    }
  };

  return (
    <div className="bg-dark-950/80 border border-slate-800 rounded-lg p-3 my-2 text-xs">
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <div className="p-1 rounded bg-blue-500/10 text-brand-blue border border-blue-500/20">
            <Wrench className="w-3.5 h-3.5" />
          </div>
          <span className="font-mono font-semibold text-slate-200">
            {trace.tool_name}
          </span>
          {getStatusBadge()}
        </div>

        <div className="flex items-center gap-1.5 text-slate-400 font-mono text-[11px]">
          <Clock className="w-3 h-3 text-slate-500" />
          <span>{formatMs(trace.latency_ms)}</span>
        </div>
      </div>

      <div className="bg-dark-900/60 p-2 rounded border border-slate-800/60 font-mono text-[11px] mb-2">
        <span className="text-slate-500 font-sans font-medium text-[10px] block mb-0.5">Input Arguments:</span>
        <span className="text-slate-300">
          {JSON.stringify(trace.input)}
        </span>
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-[11px] text-slate-400">
          {trace.output?.reason || trace.output?.message || `${trace.tool_name} completed`}
        </span>
        <button
          onClick={() => setShowRaw(!showRaw)}
          className="text-[11px] text-brand-blue hover:underline flex items-center gap-1"
        >
          {showRaw ? 'Hide raw output' : 'View raw output'}
          {showRaw ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        </button>
      </div>

      {showRaw && (
        <div className="mt-2 p-2 bg-slate-950 rounded border border-slate-800 font-mono text-[10px] text-slate-300 overflow-x-auto">
          <pre>{JSON.stringify(trace.output, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
