import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import ErrorPage from './ErrorPage';

describe('ErrorPage', () => {
  it('renders a friendly message for missing routes', () => {
    render(
      <MemoryRouter>
        <ErrorPage
          code="404"
          title="Signal lost in the mesh"
          description="The page you requested is not part of this workspace."
          actionLabel="Back home"
        />
      </MemoryRouter>
    );

    expect(screen.getByText('404')).toBeTruthy();
    expect(screen.getByText(/Signal lost in the mesh/i)).toBeTruthy();
    expect(screen.getByRole('link', { name: /back home/i })).toBeTruthy();
  });
});
