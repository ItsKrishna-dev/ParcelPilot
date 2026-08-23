import { fetchApi } from './client';
import { ChatResponse } from '../types/api';

export interface ChatHistoryItem {
  role: 'user' | 'assistant';
  content: string;
}

export async function sendChatMessage(
  message: string,
  sessionId: string,
  history?: ChatHistoryItem[]
): Promise<ChatResponse> {
  return fetchApi<ChatResponse>(
    '/chat',
    {
      method: 'POST',
      body: JSON.stringify({
        message,
        history: history || [],
      }),
    },
    sessionId
  );
}
