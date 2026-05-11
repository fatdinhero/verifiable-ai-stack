import { validateHalal, AQIDAH_AXIOMS } from './core/sharia-compliance';
import { runRibaTests } from './core/riba-detector';

console.log('\n🕌 ═══════════════════════════════════════════');
console.log('   BISMILLAH IR-RAHMAN IR-RAHIM');
console.log('   Civilization Operating System v0.1');
console.log('   Sharia-Compliance Test Suite');
console.log('   ═══════════════════════════════════════════\n');

console.log('📜 Aqidah-Axiome (Unveränderlich):');
console.log('   • Tawhid:', AQIDAH_AXIOMS.TAWHID ? '✅' : '❌');
console.log('   • Riba verboten:', AQIDAH_AXIOMS.RIBA_FORBIDDEN ? '✅' : '❌');
console.log('   • Gharar verboten:', AQIDAH_AXIOMS.GHARAR_FORBIDDEN ? '✅' : '❌');
console.log('   • Maysir verboten:', AQIDAH_AXIOMS.MAYSIR_FORBIDDEN ? '✅' : '❌');
console.log('   • Zakāt verpflichtend:', AQIDAH_AXIOMS.ZAKĀT_MANDATORY ? '✅' : '❌');
console.log('   • Nur Halal:', AQIDAH_AXIOMS.HALAL_ONLY ? '✅' : '❌');

console.log('\n🔍 HALAL-VALIDATOR TEST SUITE');
console.log('═══════════════════════════════════════════\n');

validateHalal('alcohol');
validateHalal('food', true);
validateHalal('crypto');
validateHalal('pork');
validateHalal('halal_burger', true);

runRibaTests();

console.log('🕌 Alhamdulillah - All Tests Completed!\n');
