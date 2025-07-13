/// <reference types="@testing-library/jest-dom" />
import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)
import RoiReview from '../pages/RoiReview'
import { AuthProvider } from '../context/AuthContext'
import { BrowserRouter } from 'react-router-dom'
import { api } from '../lib/api'

const rows = [
  { asin: 'A1', title: 'Item 1', vendor_id: 1, cost: 1, freight: 1, fees: 1, roi_pct: 10 },
]

describe('ROI Review page', () => {
  it('renders table rows from API', async () => {
    const get = vi.spyOn(api, 'get').mockResolvedValue({ data: rows } as any)
    const post = vi.spyOn(api, 'post').mockResolvedValue({} as any)

    const { container } = render(
      <AuthProvider>
        <BrowserRouter>
          <RoiReview />
        </BrowserRouter>
      </AuthProvider>
    )
    await waitFor(() => expect(get).toHaveBeenCalled())
    expect(screen.getByText('Item 1')).toBeInTheDocument()
    const checkbox = container.querySelector('tbody input[type="checkbox"]') as HTMLInputElement
    checkbox.click()
    screen.getByText('Approve Selected').click()
    await waitFor(() => expect(post).toHaveBeenCalledWith('/roi-review/approve', { asins: ['A1'] }))
  })
})
