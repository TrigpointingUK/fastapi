import { useEffect, useRef } from 'react';
import PhotoSwipe from 'photoswipe';
import type { Photo } from '../lib/api';

export interface PhotoSwipeOptions {
  photos: Photo[];
  initialIndex?: number;
  onClose?: () => void;
}

// Helper function to create metadata overlay HTML
function createMetadataOverlay(photo: Photo): string {
  const photoTypes: Record<string, string> = {
    'T': 'Trigpoint',
    'F': 'Flush Bracket',
    'L': 'Landscape',
    'P': 'People',
    'O': 'Other',
  };

  const licenses: Record<string, string> = {
    'Y': 'Public Domain',
    'C': 'Creative Commons',
    'N': 'Private',
  };

  const typeLabel = photoTypes[photo.type] || photo.type;
  const licenseLabel = licenses[photo.license] || photo.license;
  const filesize = (photo.filesize / 1024).toFixed(0); // Convert to KB

  return `
    <div class="pswp__custom-caption">
      <div class="pswp__caption-content">
        <h3 class="pswp__caption-title">${photo.caption || 'Untitled'}</h3>
        ${photo.text_desc ? `<p class="pswp__caption-desc">${photo.text_desc}</p>` : ''}
        <div class="pswp__caption-meta">
          <span class="pswp__caption-meta-item">Type: ${typeLabel}</span>
          <span class="pswp__caption-meta-item">License: ${licenseLabel}</span>
          <span class="pswp__caption-meta-item">${photo.width}×${photo.height}</span>
          <span class="pswp__caption-meta-item">${filesize} KB</span>
        </div>
        <div class="pswp__caption-links">
          <a href="/logs/${photo.log_id}" class="pswp__caption-link">View Log</a>
          <a href="/profile/${photo.user_id}" class="pswp__caption-link">View User</a>
        </div>
      </div>
    </div>
  `;
}

export function usePhotoSwipe({ photos, initialIndex = 0, onClose }: PhotoSwipeOptions) {
  const pswpRef = useRef<PhotoSwipe | null>(null);

  useEffect(() => {
    if (photos.length === 0) return;

    // Convert Photo objects to PhotoSwipe data source format
    const dataSource = photos.map((photo) => ({
      src: photo.photo_url,
      width: photo.width,
      height: photo.height,
      alt: photo.caption,
      // Store the full photo object for metadata display
      photo: photo,
    }));

    // PhotoSwipe options
    const options = {
      dataSource,
      index: initialIndex,
      
      // Zoom configuration
      maxZoomLevel: 4, // 400% max zoom
      initialZoomLevel: 'fit' as const, // Start with image fitted to screen (shows full image)
      secondaryZoomLevel: 1, // Double-click zooms to 1:1 (actual pixels)
      
      // UI configuration
      padding: { top: 50, bottom: 120, left: 20, right: 20 }, // Extra bottom padding for metadata
      bgOpacity: 0.9,
      
      // Hide default UI elements (we'll add custom metadata overlay)
      zoom: true,
      close: true,
      counter: false, // No counter since we're showing single photo (requirement 1b)
      arrowPrev: false, // No navigation arrows (requirement 1b)
      arrowNext: false,
      
      // Click/tap behavior
      clickToCloseNonZoomable: true,
      tapAction: () => {
        // Single tap/click closes the viewer
        if (pswpRef.current && pswpRef.current.currSlide?.currZoomLevel === pswpRef.current.currSlide?.zoomLevels.initial) {
          pswpRef.current.close();
        }
      },
      doubleTapAction: 'zoom' as const, // Double-click/tap to zoom
      
      // Mouse wheel zoom
      wheelToZoom: true,
      
      // Keyboard shortcuts
      keyboard: true,
      
      // Pinch to zoom on mobile
      pinchToClose: false,
      
      // Animation
      showHideAnimationType: 'zoom' as const, // Zoom animation on open/close
      
      // Allow panning when zoomed
      allowPanToNext: false, // Disable swipe to next since we only show one photo
      
      // Prevent closing when clicking outside if zoomed
      closeOnVerticalDrag: true,
    };

    // Create and open PhotoSwipe
    const pswp = new PhotoSwipe(options);
    pswpRef.current = pswp;

    // Add custom metadata overlay
    pswp.on('uiRegister', () => {
      pswp.ui?.registerElement({
        name: 'custom-caption',
        order: 9,
        isButton: false,
        appendTo: 'root',
        html: '',
        onInit: (el: HTMLElement) => {
          pswp.on('change', () => {
            const currSlideElement = pswp.currSlide?.data;
            if (currSlideElement && 'photo' in currSlideElement) {
              el.innerHTML = createMetadataOverlay(currSlideElement.photo as Photo);
            }
          });
        },
      });
    });

    // Add keyboard event listeners for +/- zoom (PhotoSwipe handles ESC by default)
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!pswp.currSlide) return;
      
      if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        const currZoom = pswp.currSlide.currZoomLevel || 1;
        const newZoom = Math.min(currZoom * 1.2, 4); // Increase by 20%, max 4x
        pswp.currSlide.zoomTo(newZoom, { x: pswp.currSlide.bounds.center.x, y: pswp.currSlide.bounds.center.y }, 300);
      } else if (e.key === '-' || e.key === '_') {
        e.preventDefault();
        const currZoom = pswp.currSlide.currZoomLevel || 1;
        const initialZoom = pswp.currSlide.zoomLevels.initial || 1;
        const newZoom = Math.max(currZoom / 1.2, initialZoom); // Decrease by 20%, min initial zoom
        pswp.currSlide.zoomTo(newZoom, { x: pswp.currSlide.bounds.center.x, y: pswp.currSlide.bounds.center.y }, 300);
      }
    };

    pswp.on('bindEvents', () => {
      document.addEventListener('keydown', handleKeyDown);
    });

    // Handle close event
    pswp.on('close', () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (onClose) {
        onClose();
      }
    });

    // Open PhotoSwipe
    pswp.init();

    // Cleanup on unmount
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      if (pswpRef.current) {
        pswpRef.current.close();
        pswpRef.current = null;
      }
    };
  }, [photos, initialIndex, onClose]);

  return pswpRef;
}

