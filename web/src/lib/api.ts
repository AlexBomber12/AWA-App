import axios from 'axios'
import useSWR from 'swr'

export const api = axios.create({ baseURL: '/api', withCredentials: true })

export const useKpi = () =>
  useSWR('/stats/kpi', () => api.get('/stats/kpi').then((r) => r.data))

export const useRoiByVend = () =>
  useSWR('/stats/roi_by_vendor', () =>
    api.get('/stats/roi_by_vendor').then((r) => r.data),
  )

export const useRoiTrend = () =>
  useSWR('/stats/roi_trend', () => api.get('/stats/roi_trend').then((r) => r.data))

export const useRoiTable = (params: string) =>
  useSWR(`/roi-review?${params}`, () => api.get(`/roi-review?${params}`).then((r) => r.data))
