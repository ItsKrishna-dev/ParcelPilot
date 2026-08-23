import React, { useEffect, useState } from 'react';
import { Package, RefreshCw, AlertCircle, Calendar, ShieldCheck } from 'lucide-react';
import { MockSession } from '../../types/auth';
import { OrderRecord } from '../../types/api';
import { fetchOrders } from '../../api/records';
import { Card } from '../shared/Card';
import { Badge } from '../shared/Badge';
import { LoadingSkeleton } from '../shared/LoadingSkeleton';
import { EmptyState } from '../shared/EmptyState';
import { formatDate } from '../../lib/utils';

interface OrdersViewProps {
  session: MockSession;
}

export const OrdersView: React.FC<OrdersViewProps> = ({ session }) => {
  const [orders, setOrders] = useState<OrderRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchOrders(session.sessionId);
      setOrders(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load orders.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [session.sessionId]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'BOOKED':
        return <Badge variant="blue">BOOKED</Badge>;
      case 'PICKED_UP':
        return <Badge variant="amber">PICKED_UP</Badge>;
      case 'DELIVERED':
        return <Badge variant="emerald">DELIVERED</Badge>;
      case 'DRAFT':
        return <Badge variant="slate">DRAFT</Badge>;
      default:
        return <Badge variant="slate">{status}</Badge>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Package className="w-5 h-5 text-brand-blue" />
            {session.role === 'customer' ? 'My Account Orders' : 'All System Orders'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {session.role === 'customer'
              ? `Filtered for account ${session.accountId} via PostgreSQL RLS`
              : 'Support Operations View — Multi-tenant Order Access'}
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="glass-panel px-3 py-1.5 rounded-lg border border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1.5"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      {isLoading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
          <LoadingSkeleton className="h-16 w-full" />
        </div>
      ) : orders.length === 0 ? (
        <EmptyState
          icon={Package}
          title="No Orders Found"
          description="There are currently no orders registered under this account session."
        />
      ) : (
        <div className="glass-panel rounded-xl border border-slate-800 overflow-hidden shadow-glass-md">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-dark-900 border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Order ID</th>
                  <th className="py-3 px-4">Account</th>
                  <th className="py-3 px-4">Carrier</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Booked At</th>
                  <th className="py-3 px-4">Shipment Fee</th>
                  <th className="py-3 px-4">Fault Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                {orders.map((ord) => (
                  <tr key={ord.order_id} className="hover:bg-slate-800/40 transition-colors">
                    <td className="py-3 px-4 font-bold text-slate-100">{ord.order_id}</td>
                    <td className="py-3 px-4 text-slate-400">{ord.account_id}</td>
                    <td className="py-3 px-4 font-sans font-medium text-brand-cyan">{ord.carrier}</td>
                    <td className="py-3 px-4 font-sans">{getStatusBadge(ord.status)}</td>
                    <td className="py-3 px-4 text-slate-400">{formatDate(ord.booked_at)}</td>
                    <td className="py-3 px-4 text-emerald-400 font-bold">
                      ₹{ord.shipment_fee_inr.toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 px-4 font-sans">
                      {ord.carrier_fault ? (
                        <Badge variant="red" size="sm">Carrier Fault</Badge>
                      ) : ord.customer_fault ? (
                        <Badge variant="amber" size="sm">Customer Fault</Badge>
                      ) : (
                        <span className="text-slate-500 text-[11px]">Normal</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
