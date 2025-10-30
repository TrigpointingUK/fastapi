import { describe, it, expect, beforeEach } from 'vitest';
import {
  getViewedRanges,
  addViewedRange,
  clearHistory,
  isPhotoViewed,
  getHistoryStats,
} from '../photoHistory';

describe('photoHistory', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
  });

  describe('getViewedRanges', () => {
    it('should return empty array when no history exists', () => {
      expect(getViewedRanges()).toEqual([]);
    });

    it('should return stored ranges', () => {
      const ranges = [{ min: 100, max: 200 }];
      localStorage.setItem('triguk_photo_viewing_history', JSON.stringify(ranges));
      expect(getViewedRanges()).toEqual(ranges);
    });

    it('should handle corrupted localStorage data gracefully', () => {
      localStorage.setItem('triguk_photo_viewing_history', 'invalid json');
      expect(getViewedRanges()).toEqual([]);
    });
  });

  describe('isPhotoViewed', () => {
    it('should return false for empty ranges', () => {
      expect(isPhotoViewed(100, [])).toBe(false);
    });

    it('should return true when photo is in a range', () => {
      const ranges = [
        { min: 100, max: 200 },
        { min: 300, max: 400 },
      ];
      expect(isPhotoViewed(150, ranges)).toBe(true);
      expect(isPhotoViewed(350, ranges)).toBe(true);
      expect(isPhotoViewed(100, ranges)).toBe(true); // boundary
      expect(isPhotoViewed(200, ranges)).toBe(true); // boundary
    });

    it('should return false when photo is not in any range', () => {
      const ranges = [
        { min: 100, max: 200 },
        { min: 300, max: 400 },
      ];
      expect(isPhotoViewed(50, ranges)).toBe(false);
      expect(isPhotoViewed(250, ranges)).toBe(false);
      expect(isPhotoViewed(500, ranges)).toBe(false);
    });
  });

  describe('addViewedRange', () => {
    it('should add a new range when storage is empty', () => {
      addViewedRange(100, 200);
      const ranges = getViewedRanges();
      expect(ranges).toEqual([{ min: 100, max: 200 }]);
    });

    it('should merge overlapping ranges', () => {
      addViewedRange(100, 200);
      addViewedRange(150, 250); // overlaps with previous
      const ranges = getViewedRanges();
      expect(ranges).toEqual([{ min: 100, max: 250 }]);
    });

    it('should merge adjacent ranges', () => {
      addViewedRange(100, 200);
      addViewedRange(201, 300); // adjacent
      const ranges = getViewedRanges();
      expect(ranges).toEqual([{ min: 100, max: 300 }]);
    });

    it('should keep separate non-overlapping ranges', () => {
      addViewedRange(100, 200);
      addViewedRange(300, 400); // separate range
      const ranges = getViewedRanges();
      expect(ranges).toHaveLength(2);
      expect(ranges).toContainEqual({ min: 100, max: 200 });
      expect(ranges).toContainEqual({ min: 300, max: 400 });
    });

    it('should merge multiple overlapping ranges', () => {
      addViewedRange(100, 200);
      addViewedRange(300, 400);
      addViewedRange(150, 350); // bridges both ranges
      const ranges = getViewedRanges();
      expect(ranges).toEqual([{ min: 100, max: 400 }]);
    });

    it('should handle localStorage errors gracefully', () => {
      // Mock localStorage.setItem to throw
      const originalSetItem = localStorage.setItem;
      localStorage.setItem = () => {
        throw new Error('Storage full');
      };

      // Should not throw
      expect(() => addViewedRange(100, 200)).not.toThrow();

      // Restore
      localStorage.setItem = originalSetItem;
    });
  });

  describe('clearHistory', () => {
    it('should remove all stored ranges', () => {
      addViewedRange(100, 200);
      addViewedRange(300, 400);
      expect(getViewedRanges()).toHaveLength(2);

      clearHistory();
      expect(getViewedRanges()).toEqual([]);
    });

    it('should not throw when no history exists', () => {
      expect(() => clearHistory()).not.toThrow();
    });
  });

  describe('getHistoryStats', () => {
    it('should return zero stats when no history', () => {
      const stats = getHistoryStats();
      expect(stats.rangeCount).toBe(0);
      expect(stats.totalPhotosViewed).toBe(0);
    });

    it('should count ranges correctly', () => {
      addViewedRange(100, 200);
      addViewedRange(300, 400);
      const stats = getHistoryStats();
      expect(stats.rangeCount).toBe(2);
    });

    it('should calculate total photos viewed correctly', () => {
      addViewedRange(100, 110); // 11 photos
      addViewedRange(200, 220); // 21 photos
      const stats = getHistoryStats();
      expect(stats.totalPhotosViewed).toBe(32);
    });

    it('should handle single-photo ranges', () => {
      addViewedRange(100, 100); // 1 photo
      const stats = getHistoryStats();
      expect(stats.totalPhotosViewed).toBe(1);
    });
  });
});

