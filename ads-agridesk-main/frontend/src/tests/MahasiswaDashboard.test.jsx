import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import MahasiswaDashboard from '../pages/MahasiswaDashboard';

// Mock matchMedia for window
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock api to return an empty list initially to test loading and empty state
vi.mock('../api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: { items: [], total: 0, page: 1, size: 100 } }),
  },
}));

describe('MahasiswaDashboard Component', () => {
  it('renders correctly and shows empty state when no data', async () => {
    render(
      <BrowserRouter>
        <MahasiswaDashboard />
      </BrowserRouter>
    );
    
    // Wait for async fetch to complete
    const heading = await screen.findByText(/Riwayat/i);
    expect(heading).toBeInTheDocument();
    
    // It should display the empty state message
    expect(screen.getByText(/Belum ada pengajuan/i)).toBeInTheDocument();
  });
});
