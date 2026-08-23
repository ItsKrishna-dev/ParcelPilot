import { fetchApi } from './client';
import { InsightsResponse } from '../types/api';

export async function getInternalInsights(
  sessionId: string
): Promise<InsightsResponse> {
  return fetchApi<InsightsResponse>('/internal/insights', {}, sessionId);
}
