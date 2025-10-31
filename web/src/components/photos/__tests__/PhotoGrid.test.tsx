import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import '@testing-library/jest-dom/vitest';
import PhotoGrid from '../PhotoGrid';
import { Photo } from '../../../lib/api';

// Helper to render with router
const renderWithRouter = (ui: React.ReactElement) => {
  return render(<BrowserRouter>{ui}</BrowserRouter>);
};

describe('PhotoGrid', () => {
  const mockPhotos: Photo[] = [
    {
      id: 1,
      log_id: 100,
      user_id: 1,
      icon_url: 'icon1.jpg',
      photo_url: 'photo1.jpg',
      caption: 'Photo 1',
      type: 'T',
      filesize: 1024000,
      height: 1200,
      width: 1600,
      icon_filesize: 10240,
      icon_height: 150,
      icon_width: 200,
      text_desc: 'Test description',
      license: 'Y',
    },
    {
      id: 2,
      log_id: 100,
      user_id: 1,
      icon_url: 'icon2.jpg',
      photo_url: 'photo2.jpg',
      caption: 'Photo 2',
      type: 'L',
      filesize: 2048000,
      height: 1200,
      width: 1600,
      icon_filesize: 10240,
      icon_height: 150,
      icon_width: 200,
      text_desc: 'Test description',
      license: 'Y',
    },
    {
      id: 3,
      log_id: 100,
      user_id: 1,
      icon_url: 'icon3.jpg',
      photo_url: 'photo3.jpg',
      caption: 'Photo 3',
      type: 'O',
      filesize: 1536000,
      height: 1200,
      width: 1600,
      icon_filesize: 10240,
      icon_height: 150,
      icon_width: 200,
      text_desc: 'Test description',
      license: 'Y',
    },
  ];

  it('should render all photos', () => {
    renderWithRouter(<PhotoGrid photos={mockPhotos} />);
    const images = screen.getAllByRole('img');
    expect(images).toHaveLength(3);
  });

  it('should render empty state when no photos', () => {
    renderWithRouter(<PhotoGrid photos={[]} />);
    expect(screen.getByText('No photos found')).toBeInTheDocument();
  });

  it('should call onPhotoClick when a photo is clicked', () => {
    const handleClick = vi.fn();
    renderWithRouter(<PhotoGrid photos={mockPhotos} onPhotoClick={handleClick} />);
    
    const firstPhoto = screen.getAllByRole('img')[0];
    fireEvent.click(firstPhoto);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(handleClick).toHaveBeenCalledWith(mockPhotos[0]);
  });

  it('should not throw when onPhotoClick is not provided', () => {
    renderWithRouter(<PhotoGrid photos={mockPhotos} />);
    const firstPhoto = screen.getAllByRole('img')[0];
    
    expect(() => fireEvent.click(firstPhoto)).not.toThrow();
  });

  it('should render grid layout', () => {
    const { container } = renderWithRouter(<PhotoGrid photos={mockPhotos} />);
    const grid = container.querySelector('.grid');
    expect(grid).toBeInTheDocument();
    expect(grid).toHaveClass('grid-cols-1');
    expect(grid).toHaveClass('md:grid-cols-2');
    expect(grid).toHaveClass('lg:grid-cols-3');
  });

  it('should handle null photos array', () => {
    renderWithRouter(<PhotoGrid photos={null as unknown as Photo[]} />);
    expect(screen.getByText('No photos found')).toBeInTheDocument();
  });

  it('should pass correct props to PhotoThumbnail components', () => {
    renderWithRouter(<PhotoGrid photos={mockPhotos} />);
    const images = screen.getAllByRole('img');
    
    // PhotoThumbnail uses photo_url (not icon_url)
    expect(images[0]).toHaveAttribute('src', 'photo1.jpg');
    expect(images[1]).toHaveAttribute('src', 'photo2.jpg');
    expect(images[2]).toHaveAttribute('src', 'photo3.jpg');
  });
});

