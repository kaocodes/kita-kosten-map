/** Exact rational arithmetic keeps income boundaries and half-cent rounding stable. */
export class Fraction {
  readonly numerator: bigint;
  readonly denominator: bigint;

  constructor(numerator: bigint | number, denominator: bigint | number = 1) {
    const n = BigInt(numerator);
    const d = BigInt(denominator);
    if (d === 0n) throw new RangeError("A fraction cannot have a zero denominator.");
    const sign = d < 0n ? -1n : 1n;
    let a = n < 0n ? -n : n;
    let b = d < 0n ? -d : d;
    while (b !== 0n) [a, b] = [b, a % b];
    this.numerator = sign * n / a;
    this.denominator = sign * d / a;
  }

  add(other: Fraction | number): Fraction {
    const value = fraction(other);
    return new Fraction(this.numerator * value.denominator + value.numerator * this.denominator,
      this.denominator * value.denominator);
  }

  multiply(other: Fraction | number): Fraction {
    const value = fraction(other);
    return new Fraction(this.numerator * value.numerator, this.denominator * value.denominator);
  }

  divide(other: Fraction | number): Fraction {
    const value = fraction(other);
    return new Fraction(this.numerator * value.denominator, this.denominator * value.numerator);
  }

  compare(other: Fraction | number): number {
    const value = fraction(other);
    const difference = this.numerator * value.denominator - value.numerator * this.denominator;
    return difference < 0n ? -1 : difference > 0n ? 1 : 0;
  }
}

export function fraction(value: Fraction | number): Fraction {
  return value instanceof Fraction ? value : new Fraction(value);
}

export function safeInteger(value: bigint): number {
  const result = Number(value);
  if (!Number.isSafeInteger(result)) throw new RangeError("The result exceeds the safe integer range.");
  return result;
}

export function roundMoney(value: Fraction | number, rule = "cent_half_up"): number {
  const amount = fraction(value);
  const quantum = rule === "whole_euro_half_up" ? 100n : 1n;
  const sign = amount.numerator < 0n ? -1n : 1n;
  const absolute = amount.numerator * sign;
  const denominator = amount.denominator * quantum;
  const rounded = (2n * absolute + denominator) / (2n * denominator);
  return safeInteger(sign * rounded * quantum);
}
