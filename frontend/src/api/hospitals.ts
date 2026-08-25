import api from './client'

export interface Hospital {
  id: number
  name: string
}

export const getHospitals = async (): Promise<Hospital[]> =>
  (await api.get<Hospital[]>('/hospitals')).data
