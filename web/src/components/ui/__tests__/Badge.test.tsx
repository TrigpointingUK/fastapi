import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import Badge from '../Badge';

describe('Badge', () => {
  it('should render children', () => {
    render(<Badge>Test badge</Badge>);
    expect(screen.getByText('Test badge')).toBeInTheDocument();
  });

  it('should apply default variant classes', () => {
    render(<Badge>Default</Badge>);
    const badge = screen.getByText('Default');
    expect(badge).toHaveClass('bg-blue-100');
    expect(badge).toHaveClass('text-blue-800');
  });

  it('should apply good variant classes', () => {
    render(<Badge variant="good">Good</Badge>);
    const badge = screen.getByText('Good');
    expect(badge).toHaveClass('bg-green-100');
    expect(badge).toHaveClass('text-green-800');
  });

  it('should apply damaged variant classes', () => {
    render(<Badge variant="damaged">Damaged</Badge>);
    const badge = screen.getByText('Damaged');
    expect(badge).toHaveClass('bg-yellow-100');
    expect(badge).toHaveClass('text-yellow-800');
  });

  it('should apply missing variant classes', () => {
    render(<Badge variant="missing">Missing</Badge>);
    const badge = screen.getByText('Missing');
    expect(badge).toHaveClass('bg-red-100');
    expect(badge).toHaveClass('text-red-800');
  });

  it('should apply unknown variant classes', () => {
    render(<Badge variant="unknown">Unknown</Badge>);
    const badge = screen.getByText('Unknown');
    expect(badge).toHaveClass('bg-gray-100');
    expect(badge).toHaveClass('text-gray-800');
  });

  it('should apply custom className', () => {
    render(<Badge className="custom-class">Badge</Badge>);
    const badge = screen.getByText('Badge');
    expect(badge).toHaveClass('custom-class');
    // Should still have base classes
    expect(badge).toHaveClass('inline-flex');
  });

  it('should have correct base styling', () => {
    render(<Badge>Badge</Badge>);
    const badge = screen.getByText('Badge');
    expect(badge).toHaveClass('inline-flex');
    expect(badge).toHaveClass('items-center');
    expect(badge).toHaveClass('rounded-full');
    expect(badge).toHaveClass('text-xs');
    expect(badge).toHaveClass('font-medium');
  });
});

