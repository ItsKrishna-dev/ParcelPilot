import React, { useEffect, useState } from 'react';
import { Activity, RefreshCw, AlertCircle, ShieldAlert, BarChart3 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { MockSession } from '../../types/auth';
import { InsightsResponse } from '../../types/api';
import { getInternalInsights } from '../../api/insights';
import { SLARiskTable } from './SLARiskTable';
import { IssueClustersCard } from './IssueClustersCard';
import { LoadingSkeleton } from '../shared/LoadingSkeleton';
import { Card } from '../shared/Card';

interface InsightsDashboardProps {
  session: MockSession;
  view?: 'sla_risk' | 'issue_clusters';
}

export const InsightsDashboard: React.FC<InsightsDashboardProps> = ({
  session,
  view = 'sla_risk',
}) => {
  const [data, setData] = useState<InsightsResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const res = await getInternalInsights(session.sessionId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load internal proactive insights.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [session.sessionId]);

  // Chart data from volume anomalies
  const chartData = (data?.ticket_volume_anomalies || []).map((a) => ({
    name: a.product_area,
    'Rolling Volume': a.rolling_count,
    'Baseline Avg': a.baseline_avg,
    isSpike: a.is_spike,
  }));

  const isSlaView = view === 'sla_risk';

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="w-5 h-5 text-brand-blue" />
            {isSlaView ? 'SLA Risk Dashboard & Predictions' : 'Cross-Account Issue Clusters & Correlations'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {isSlaView
              ? 'Real-time SLA breach predictions and rolling ticket volumes as of'
              : 'Statistical anomalies and platform-wide correlated issues as of'}{' '}
            <strong className="text-slate-300">{data?.as_of || 'snapshot time'}</strong>
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="glass-panel px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Insights
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-4">
          <LoadingSkeleton className="h-48 w-full" />
          <LoadingSkeleton className="h-64 w-full" />
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* Chart Section */}
          {chartData.length > 0 && (
            <Card className="border border-slate-800 bg-dark-900/90">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-bold text-slate-100 flex items-center gap-2">
                  <BarChart3 className="w-4 h-4 text-brand-cyan" />
                  Ticket Volume Anomalies by Product Area
                </h3>
                <span className="text-xs text-slate-400 font-mono">Z-Score Spike Detection</span>
              </div>

              <div className="h-56 w-full text-xs">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} />
                    <YAxis stroke="#94a3b8" fontSize={11} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0d1322',
                        borderColor: '#1e293b',
                        color: '#f8fafc',
                        borderRadius: '8px',
                        fontSize: '12px',
                      }}
                    />
                    <Bar dataKey="Rolling Volume" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="Baseline Avg" fill="#475569" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}

          {/* Render table or clusters card depending on the view prop */}
          {isSlaView ? (
            <SLARiskTable entries={data.sla_risk || []} />
          ) : (
            <IssueClustersCard
              correlations={data.cross_account_correlations || []}
              anomalies={data.ticket_volume_anomalies || []}
            />
          )}
        </div>
      ) : null}
    </div>
  );
};
