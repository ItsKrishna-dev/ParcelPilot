import { fetchApi } from './client';
import { ChatResponse } from '../types/api';

export async function sendChatMessage(
  message: string,
  sessionId: string
): Promise<ChatResponse> {
  return fetchApi<ChatResponse>(
    '/chat',
    {
      method: 'POST',
      body: JSON.stringify({ message }),
    },
    sessionId
  );
}
