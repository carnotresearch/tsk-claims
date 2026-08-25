import api from './client'
import type { ChatSession, ChatMessage } from '../types'

export const createSession = async (title?: string): Promise<ChatSession> =>
  (await api.post<ChatSession>('/chat/sessions', { title: title ?? 'New Chat' })).data

export const getSessions = async (): Promise<ChatSession[]> =>
  (await api.get<ChatSession[]>('/chat/sessions')).data

export const getMessages = async (sessionId: number): Promise<ChatMessage[]> =>
  (await api.get<ChatMessage[]>(`/chat/sessions/${sessionId}/messages`)).data

export const sendMessage = async (sessionId: number, content: string): Promise<ChatMessage> =>
  (await api.post<ChatMessage>(`/chat/sessions/${sessionId}/messages`, { content })).data

export const deleteSession = async (sessionId: number): Promise<void> => {
  await api.delete(`/chat/sessions/${sessionId}`)
}
