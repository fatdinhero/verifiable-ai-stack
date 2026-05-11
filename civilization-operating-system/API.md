# COS Backend API Documentation

## Riba Detection

### `detectRiba(transaction: Transaction): boolean`

Detects if a transaction contains Riba (interest).

**Parameters:**
- `transaction.amount` (number) - Transaction amount
- `transaction.profit_loss_sharing` (boolean) - Is profit/loss shared?
- `transaction.time_based_interest` (boolean) - Is there time-based interest?
- `transaction.risk_distribution` ('symmetric' | 'asymmetric') - Risk distribution
- `transaction.guaranteed_return?` (boolean) - Is return guaranteed?
- `transaction.description?` (string) - Optional description

**Returns:** `boolean`
- `true` = RIBA detected (HARAM)
- `false` = No Riba (HALAL)

**Example:**
```typescript
const result = detectRiba({
  amount: 10000,
  profit_loss_sharing: true,
  time_based_interest: false,
  risk_distribution: 'symmetric'
});
// Returns: false (HALAL)
```

---

## Zakāt Calculation

### `calculateZakāt(wealth: number, nisab_threshold?: number): number`

Calculates Zakāt (2.5%) on wealth above Nisab.

**Parameters:**
- `wealth` (number) - Total wealth in currency units
- `nisab_threshold?` (number) - Nisab threshold (default: 595)

**Returns:** `number` - Zakāt amount due

**Example:**
```typescript
const zakāt = calculateZakāt(100000); // €100,000
// Returns: 2500 (€2,500)
```

---

## Halal Validation

### `validateHalal(category: string, ulama_certified?: boolean): HalalStatus`

Validates if a category is Halal, Haram, or Mashbooh.

**Parameters:**
- `category` (string) - Category to validate
- `ulama_certified?` (boolean) - Is it Ulama certified? (default: false)

**Returns:** `HalalStatus`
- `'halal'` - Permissible
- `'haram'` - Forbidden
- `'mashbooh'` - Doubtful

**Example:**
```typescript
const status = validateHalal('food', true);
// Returns: 'halal'
```

---

## Error Handling

All functions may throw:
- `ValidationError` - Invalid input
- `MissingFieldError` - Required field missing
- `RangeError` - Value out of range
- `RibaDetectedError` - Riba detected
- `ShariaComplianceError` - Sharia violation

**Example:**
```typescript
try {
  const result = detectRiba(transaction);
} catch (error) {
  if (error instanceof ValidationError) {
    console.error('Invalid input:', error.message);
  }
}
```

---

## Type Definitions
```typescript
interface Transaction {
  amount: number;
  description?: string;
  profit_loss_sharing: boolean;
  time_based_interest: boolean;
  risk_distribution: 'symmetric' | 'asymmetric';
  guaranteed_return?: boolean;
}

type Madhab = 'hanafi' | 'shafi' | 'maliki' | 'hanbali';
type HalalStatus = 'halal' | 'haram' | 'mashbooh';
```

---

**For more information:** https://github.com/fatdinhero/civilization-operating-system
