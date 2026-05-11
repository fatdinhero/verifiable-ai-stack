/**
 * Riba-Detection-Algorithm
 */

export interface Transaction {
    amount: number;
    description?: string;
    guaranteed_return?: boolean;
    profit_loss_sharing: boolean;
    time_based_interest: boolean;
    risk_distribution: 'symmetric' | 'asymmetric';
}

export function detectRiba(tx: Transaction): boolean {
    console.log(`\n🔍 Prüfe: ${tx.description || tx.amount + '€'}`);
    
    if (tx.guaranteed_return === true) {
        console.log('   ❌ RIBA: Garantierte Rendite ohne Risiko');
        return true;
    }
    
    if (tx.time_based_interest === true) {
        console.log('   ❌ RIBA: Zeitbasierter Zins');
        return true;
    }
    
    if (tx.risk_distribution === 'asymmetric') {
        console.log('   ❌ RIBA: Nur eine Partei trägt Risiko');
        return true;
    }
    
    if (!tx.profit_loss_sharing) {
        console.log('   ❌ RIBA: Kein Gewinn/Verlust-Teilung');
        return true;
    }
    
    console.log('   ✅ HALAL: Transaktion ist Riba-frei');
    return false;
}

export function calculateZakāt(wealth: number, nisab_threshold: number = 595): number {
    console.log(`\n💰 Zakāt-Berechnung für ${wealth}€`);
    
    if (wealth >= nisab_threshold) {
        const zakāt = wealth * 0.025;
        console.log(`   ✅ Zakāt fällig: ${zakāt.toFixed(2)}€ (2.5%)`);
        return zakāt;
    }
    
    console.log(`   ℹ️ Kein Zakāt (unter Nisab)`);
    return 0;
}

export function runRibaTests(): void {
    console.log('\n🧪 RIBA-DETECTION TEST SUITE');
    console.log('═══════════════════════════════════\n');
    
    const mudaraba: Transaction = {
        amount: 10000,
        description: 'Mudaraba-Vertrag',
        guaranteed_return: false,
        profit_loss_sharing: true,
        time_based_interest: false,
        risk_distribution: 'symmetric'
    };
    const test1 = !detectRiba(mudaraba);
    console.log(`Test 1 - Mudaraba: ${test1 ? '✅ PASSED' : '❌ FAILED'}`);
    
    const bank_loan: Transaction = {
        amount: 10000,
        description: 'Bank-Kredit 5% Zins',
        guaranteed_return: true,
        profit_loss_sharing: false,
        time_based_interest: true,
        risk_distribution: 'asymmetric'
    };
    const test2 = detectRiba(bank_loan);
    console.log(`Test 2 - Riba-Kredit: ${test2 ? '✅ PASSED' : '❌ FAILED'}`);
    
    console.log('\n💰 ZAKĀT-CALCULATOR TEST SUITE');
    console.log('═══════════════════════════════════\n');
    
    calculateZakāt(10000, 595);
    calculateZakāt(400, 595);
    
    console.log('\n✅ Alle Tests abgeschlossen!\n');
}
