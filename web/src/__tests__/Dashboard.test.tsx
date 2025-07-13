/// <reference types="@testing-library/jest-dom" />
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)
import Dashboard from '../pages/Dashboard'
import { AuthProvider } from '../context/AuthContext'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'

const kpiData = [
  { name: 'Total SKU', value: 10 },
  { name: 'Avg ROI %', value: 12 },
  { name: 'Approved €', value: 1000 },
  { name: 'Potential Profit €', value: 2000 },
]
const vendorData = [{ vendor: 'ACME', roi: 15 }]
const trendData = [{ date: '2024-01-01', roi: 10 }]

describe('Dashboard page', () => {
  it('loads stats and renders charts', async () => {
    const get = vi.fn()
    get
      .mockResolvedValueOnce({ data: kpiData })
      .mockResolvedValueOnce({ data: vendorData })
      .mockResolvedValueOnce({ data: trendData })
    vi.spyOn(axios, 'create').mockReturnValue({
      get,
      interceptors: { response: { use: vi.fn() } },
    } as any)

    const { container } = render(
      <AuthProvider>
        <BrowserRouter>
          <Dashboard />
        </BrowserRouter>
      </AuthProvider>
    )

    await waitFor(() => expect(get).toHaveBeenCalledTimes(3))
    expect(screen.getByText('Total SKU')).toBeInTheDocument()
    expect(container.querySelectorAll('.recharts-wrapper').length).toBe(2)
  })
})
