/**
 * BISMILLAH IR-RAHMAN IR-RAHIM
 * Civilization Operating System - Sharia Compliance Engine
 */

export const AQIDAH_AXIOMS = {
    TAWHID: true,
    RIBA_FORBIDDEN: true,
    GHARAR_FORBIDDEN: true,
    MAYSIR_FORBIDDEN: true,
    ZAKĀT_MANDATORY: true,
    HALAL_ONLY: true
} as const;

export type Madhab = 'hanafi' | 'shafi' | 'maliki' | 'hanbali';
export type HalalStatus = 'halal' | 'haram' | 'mashbooh';

export const HARAM_CATEGORIES = [
    'alcohol',
    'pork',
    'gambling',
    'interest_bearing',
    'pornography',
    'weapons_offensive'
] as const;

export interface ShariaConfig {
    madhab: Madhab;
    strictness: 'lenient' | 'moderate' | 'strict';
    ulama_review_required: boolean;
}

export const DEFAULT_SHARIA_CONFIG: ShariaConfig = {
    madhab: 'hanafi',
    strictness: 'moderate',
    ulama_review_required: true
};

export function validateHalal(
    category: string,
    ulama_certified: boolean = false
): HalalStatus {
    if (HARAM_CATEGORIES.includes(category as any)) {
        console.log(`❌ HARAM: ${category}`);
        return 'haram';
    }
    if (ulama_certified) {
        console.log(`✅ HALAL: ${category} (Ulama-zertifiziert)`);
        return 'halal';
    }
    console.log(`⚠️ MASHBOOH: ${category} (benötigt Review)`);
    return 'mashbooh';
}

console.log('🕌 Sharia-Compliance-Engine loaded');
