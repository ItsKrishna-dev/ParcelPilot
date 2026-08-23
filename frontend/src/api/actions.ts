import { fetchApi } from './client';
import { ActionEngineOutput } from '../types/api';

export async function confirmPendingAction(
  pendingActionId: string,
  actionType: string,
  payload: Record<string, any>,
  sessionId: string
): Promise<ActionEngineOutput> {
  return fetchApi<ActionEngineOutput>(
    '/actions/confirm',
    {
      method: 'POST',
      body: JSON.stringify({
        pending_action_id: pendingActionId,
        action_type: actionType,
        payload,
      }),
    },
    sessionId
  );
}
