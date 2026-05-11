/**
 * Unit Tests for Sharia Compliance Validator
 * @author Fatih Dinc
 * @copyright 2026 Fatih Dinc
 */

import { validateHalal, AQIDAH_AXIOMS, HARAM_CATEGORIES } from '../../src/core/sharia-compliance';

describe('Sharia Compliance Validator', () => {
  describe('AQIDAH_AXIOMS', () => {
    test('should have TAWHID axiom', () => {
      expect(AQIDAH_AXIOMS.TAWHID).toBe(true);
    });

    test('should forbid Riba', () => {
      expect(AQIDAH_AXIOMS.RIBA_FORBIDDEN).toBe(true);
    });

    test('should forbid Gharar', () => {
      expect(AQIDAH_AXIOMS.GHARAR_FORBIDDEN).toBe(true);
    });

    test('should forbid Maysir', () => {
      expect(AQIDAH_AXIOMS.MAYSIR_FORBIDDEN).toBe(true);
    });

    test('should mandate Zakāt', () => {
      expect(AQIDAH_AXIOMS.ZAKĀT_MANDATORY).toBe(true);
    });

    test('should require Halal only', () => {
      expect(AQIDAH_AXIOMS.HALAL_ONLY).toBe(true);
    });
  });

  describe('validateHalal', () => {
    test('should detect HARAM: alcohol', () => {
      const result = validateHalal('alcohol');
      expect(result).toBe('haram');
    });

    test('should detect HARAM: pork', () => {
      const result = validateHalal('pork');
      expect(result).toBe('haram');
    });

    test('should detect HARAM: gambling', () => {
      const result = validateHalal('gambling');
      expect(result).toBe('haram');
    });

    test('should detect HARAM: interest_bearing', () => {
      const result = validateHalal('interest_bearing');
      expect(result).toBe('haram');
    });

    test('should validate HALAL: food (with ulama certification)', () => {
      const result = validateHalal('food', true);
      expect(result).toBe('halal');
    });

    test('should return MASHBOOH: food (without ulama certification)', () => {
      const result = validateHalal('food', false);
      expect(result).toBe('mashbooh');
    });

    test('should validate HALAL: clothing (with ulama certification)', () => {
      const result = validateHalal('clothing', true);
      expect(result).toBe('halal');
    });

    test('should handle unknown categories as potentially halal', () => {
      const result = validateHalal('technology', true);
      expect(result).toBe('halal');
    });
  });

  describe('HARAM_CATEGORIES', () => {
    test('should include alcohol', () => {
      expect(HARAM_CATEGORIES).toContain('alcohol');
    });

    test('should include pork', () => {
      expect(HARAM_CATEGORIES).toContain('pork');
    });

    test('should include gambling', () => {
      expect(HARAM_CATEGORIES).toContain('gambling');
    });

    test('should include interest_bearing', () => {
      expect(HARAM_CATEGORIES).toContain('interest_bearing');
    });
  });
});
