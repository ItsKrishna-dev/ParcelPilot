import { fetchApi } from './client';
import { OrderRecord, TicketRecord, AccountRecord } from '../types/api';

export async function fetchOrders(
  sessionId: string,
  accountId?: string
): Promise<OrderRecord[]> {
  const query = accountId ? `?account_id=${encodeURIComponent(accountId)}` : '';
  const res = await fetchApi<{ orders: OrderRecord[] }>(
    `/records/orders${query}`,
    {},
    sessionId
  );
  return res.orders || [];
}

export async function fetchTickets(
  sessionId: string,
  accountId?: string,
  status?: string
): Promise<TicketRecord[]> {
  const params = new URLSearchParams();
  if (accountId) params.append('account_id', accountId);
  if (status) params.append('status', status);
  const query = params.toString() ? `?${params.toString()}` : '';

  const res = await fetchApi<{ tickets: TicketRecord[] }>(
    `/records/tickets${query}`,
    {},
    sessionId
  );
  return res.tickets || [];
}

export async function fetchAccountDetails(
  sessionId: string,
  accountId?: string
): Promise<AccountRecord | null> {
  const query = accountId ? `?account_id=${encodeURIComponent(accountId)}` : '';
  const res = await fetchApi<{ account: AccountRecord | null }>(
    `/records/account${query}`,
    {},
    sessionId
  );
  return res.account || null;
}
