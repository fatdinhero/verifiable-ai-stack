/**
 * Unit Tests for Riba Detection Algorithm
 * @author Fatih Dinc
 * @copyright 2026 Fatih Dinc
 */

import { detectRiba, calculateZakāt } from '../../src/core/riba-detector';

describe('Riba Detection Algorithm', () => {
  describe('detectRiba', () => {
    test('should detect HALAL: Mudaraba (profit-loss sharing)', () => {
      const result = detectRiba({
        amount: 10000,
        profit_loss_sharing: true,
        time_based_interest: false,
        risk_distribution: 'symmetric'
      });
      expect(result).toBe(false);
    });

    test('should detect RIBA: Guaranteed return', () => {
      const result = detectRiba({
        amount: 5000,
        guaranteed_return: true,
        profit_loss_sharing: true,
        time_based_interest: false,
        risk_distribution: 'symmetric'
      });
      expect(result).toBe(true);
    });

    test('should detect RIBA: Time-based interest', () => {
      const result = detectRiba({
        amount: 3000,
        profit_loss_sharing: true,
        time_based_interest: true,
        risk_distribution: 'symmetric'
      });
      expect(result).toBe(true);
    });

    test('should detect RIBA: Asymmetric risk distribution', () => {
      const result = detectRiba({
        amount: 8000,
        profit_loss_sharing: true,
        time_based_interest: false,
        risk_distribution: 'asymmetric'
      });
      expect(result).toBe(true);
    });

    test('should detect RIBA: No profit/loss sharing', () => {
      const result = detectRiba({
        amount: 2000,
        profit_loss_sharing: false,
        time_based_interest: false,
        risk_distribution: 'symmetric'
      });
      expect(result).toBe(true);
    });

    test('should detect HALAL: Musharaka (joint venture)', () => {
      const result = detectRiba({
        amount: 50000,
        description: 'Musharaka Real Estate',
        profit_loss_sharing: true,
        time_based_interest: false,
        risk_distribution: 'symmetric'
      });
      expect(result).toBe(false);
    });
  });

  describe('calculateZakāt', () => {
    test('should calculate 2.5% Zakāt on wealth above Nisab', () => {
      const wealth = 100000;
      const result = calculateZakāt(wealth);
      expect(result).toBe(2500); // 2.5%
    });

    test('should return 0 for wealth below Nisab', () => {
      const wealth = 500;
      const result = calculateZakāt(wealth);
      expect(result).toBe(0);
    });

    test('should handle custom Nisab threshold', () => {
      const wealth = 1000;
      const result = calculateZakāt(wealth, 500);
      expect(result).toBe(25); // 2.5% of 1000
    });

    test('should calculate correctly for large amounts', () => {
      const wealth = 1000000;
      const result = calculateZakāt(wealth);
      expect(result).toBe(25000);
    });

    test('should handle zero wealth', () => {
      const result = calculateZakāt(0);
      expect(result).toBe(0);
    });

    test('should handle exact Nisab threshold', () => {
      const wealth = 595;
      const result = calculateZakāt(wealth, 595);
      expect(result).toBe(14.875); // 2.5% of 595
    });
  });
});
