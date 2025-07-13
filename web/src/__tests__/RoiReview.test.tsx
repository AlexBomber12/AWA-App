/// <reference types="@testing-library/jest-dom" />
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)
import RoiReview from '../pages/RoiReview'
import { AuthProvider } from '../context/AuthContext'
import { BrowserRouter } from 'react-router-dom'
import axios from 'axios'

const rows = [
  { asin: 'A1', title: 'Item 1', vendor_id: 1, cost: 1, freight: 1, fees: 1, roi_pct: 10 },
]

describe('ROI Review page', () => {
  it('renders table rows from API', async () => {
    const get = vi.fn().mockResolvedValue({ data: rows })
    const post = vi.fn().mockResolvedValue({})
    vi.spyOn(axios, 'create').mockReturnValue({
      get,
      post,
      interceptors: { response: { use: vi.fn() } },
    } as any)

    render(
      <AuthProvider>
        <BrowserRouter>
          <RoiReview />
        </BrowserRouter>
      </AuthProvider>
    )

    await waitFor(() => expect(get).toHaveBeenCalled())
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    expect(screen.getByText('Approve Selected')).toBeInTheDocument()
  })
})
