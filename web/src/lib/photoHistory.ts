/**
 * Photo viewing history utility using localStorage
 * Tracks ranges of photo IDs that the user has already seen
 */

const STORAGE_KEY = 'triguk_photo_viewing_history';

export interface PhotoRange {
  min: number;
  max: number;
}

/**
 * Get all viewed photo ID ranges from localStorage
 */
export function getViewedRanges(): PhotoRange[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return [];
    return JSON.parse(stored) as PhotoRange[];
  } catch (error) {
    console.error('Failed to read photo viewing history:', error);
    return [];
  }
}

/**
 * Check if a photo ID falls within any viewed range
 */
export function isPhotoViewed(photoId: number, ranges: PhotoRange[]): boolean {
  return ranges.some(range => photoId >= range.min && photoId <= range.max);
}

/**
 * Merge overlapping or adjacent ranges (within tolerance)
 * Assumes ranges are sorted by min value
 * Tolerance allows merging ranges with small gaps (e.g., deleted photos)
 */
function mergeRanges(ranges: PhotoRange[], tolerance: number = 50): PhotoRange[] {
  if (ranges.length <= 1) return ranges;

  // Sort by min value
  const sorted = [...ranges].sort((a, b) => a.min - b.min);
  const merged: PhotoRange[] = [sorted[0]];

  for (let i = 1; i < sorted.length; i++) {
    const current = sorted[i];
    const lastMerged = merged[merged.length - 1];

    // If current range overlaps or is within tolerance of last merged range
    if (current.min <= lastMerged.max + tolerance) {
      // Extend the last merged range
      lastMerged.max = Math.max(lastMerged.max, current.max);
    } else {
      // Add as a new range
      merged.push(current);
    }
  }

  return merged;
}

/**
 * Add a new viewed range and merge with existing ranges
 */
export function addViewedRange(min: number, max: number): void {
  try {
    const ranges = getViewedRanges();
    ranges.push({ min, max });
    const merged = mergeRanges(ranges);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
  } catch (error) {
    console.error('Failed to save photo viewing history:', error);
  }
}

/**
 * Clear all viewing history
 */
export function clearHistory(): void {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear photo viewing history:', error);
  }
}

/**
 * Compact and merge existing history to reduce fragmentation
 * Call this to fix existing history with many small gaps
 */
export function compactHistory(): void {
  try {
    const ranges = getViewedRanges();
    const merged = mergeRanges(ranges);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    console.log(`Compacted ${ranges.length} ranges into ${merged.length} ranges`);
  } catch (error) {
    console.error('Failed to compact photo viewing history:', error);
  }
}

/**
 * Get statistics about viewing history
 */
export function getHistoryStats(): {
  rangeCount: number;
  totalPhotosViewed: number;
} {
  const ranges = getViewedRanges();
  const totalPhotosViewed = ranges.reduce(
    (sum, range) => sum + (range.max - range.min + 1),
    0
  );
  return {
    rangeCount: ranges.length,
    totalPhotosViewed,
  };
}

/**
 * Debug utility: Log viewing history to console
 * Useful for troubleshooting. Call from browser console: window.debugPhotoHistory()
 */
export function debugPhotoHistory(): void {
  const ranges = getViewedRanges();
  const stats = getHistoryStats();
  
  console.log('=== Photo Viewing History Debug ===');
  console.log(`Total ranges: ${stats.rangeCount}`);
  console.log(`Total photos viewed: ${stats.totalPhotosViewed.toLocaleString()}`);
  console.log('\nRanges:');
  ranges.forEach((range, i) => {
    const size = range.max - range.min + 1;
    const gap = i > 0 ? range.min - ranges[i - 1].max - 1 : 0;
    console.log(`  ${i + 1}. Photo IDs ${range.min} - ${range.max} (${size} photos)${gap > 0 ? ` [gap: ${gap}]` : ''}`);
  });
  console.log('\nTo clear history, call: window.clearPhotoHistory()');
  console.log('To compact history (merge ranges), call: window.compactPhotoHistory()');
}

// Expose debug functions globally for troubleshooting
if (typeof window !== 'undefined') {
  (window as unknown as Window & { debugPhotoHistory: typeof debugPhotoHistory; clearPhotoHistory: typeof clearHistory; compactPhotoHistory: typeof compactHistory }).debugPhotoHistory = debugPhotoHistory;
  (window as unknown as Window & { debugPhotoHistory: typeof debugPhotoHistory; clearPhotoHistory: typeof clearHistory; compactPhotoHistory: typeof compactHistory }).clearPhotoHistory = clearHistory;
  (window as unknown as Window & { debugPhotoHistory: typeof debugPhotoHistory; clearPhotoHistory: typeof clearHistory; compactPhotoHistory: typeof compactHistory }).compactPhotoHistory = compactHistory;
}

