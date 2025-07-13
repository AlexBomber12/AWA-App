/// <reference types="@testing-library/jest-dom" />
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'
import { AuthProvider } from '../context/AuthContext'

describe('Login page', () => {
  it('renders form inputs', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <Login />
        </BrowserRouter>
      </AuthProvider>
    )
    expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Password')).toBeInTheDocument()
  })
})
