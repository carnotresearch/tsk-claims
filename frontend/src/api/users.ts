import api from './client'
import type { User } from '../types'

export interface UserCreate {
  email: string
  password: string
  full_name?: string
  role: 'admin' | 'hospital_user'
  hospital_id?: number
}

export const getUsers = async (): Promise<User[]> =>
  (await api.get<User[]>('/users')).data

export const createUser = async (data: UserCreate): Promise<User> =>
  (await api.post<User>('/users', data)).data

export const updateUser = async (id: number, data: Partial<Pick<User, 'full_name' | 'is_active' | 'hospital_id'>>): Promise<User> =>
  (await api.patch<User>(`/users/${id}`, data)).data

export const deactivateUser = async (id: number): Promise<void> => {
  await api.delete(`/users/${id}`)
}
