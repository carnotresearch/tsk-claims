import api from './client'
import type { TokenResponse, User } from '../types'

export const login = async (email: string, password: string): Promise<TokenResponse> => {
  const form = new URLSearchParams({ username: email, password })
  const { data } = await api.post<TokenResponse>('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return data
}

export const getMe = async (): Promise<User> => {
  const { data } = await api.get<User>('/auth/me')
  return data
}
