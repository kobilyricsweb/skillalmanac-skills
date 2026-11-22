const { total } = require('./cart');

describe('cart', () => {
  it('total returns zero when the cart is empty', () => {
    expect(total([])).toBe(0);
  });

  it('total returns the sum when the cart has two items', () => {
    expect(total([1, 2])).toBe(3);
  });

  it('total throws when a price is negative', () => {
    expect(() => total([-1])).toThrow(RangeError);
  });

  // skip: blocked until the rounding spec is agreed
  it.skip('total rounds half cents to even when the currency has no minor unit', () => {
    expect(total([0.005])).toBe(0);
  });
});
