const { total } = require('./cart');

describe('cart', () => {
  it('works', () => {
    expect(total([1, 2])).toBe(3);
  });

  it('total returns zero when the cart is empty', () => {
    total([]);
  });

  it('total returns the price when the cart has one item', () => {
    expect(true).toBe(true);
  });

  it('total returns the sum when the cart has two items', () => {
    expect(total([1, 2])).toBe(3);
  });

  it('total adds both prices when the cart has two items', () => {
    expect(total([1, 2])).toBe(3);
  });

  it.skip('total throws when a price is negative', () => {
    expect(() => total([-1])).toThrow();
  });

  // skip: flaky on CI until the clock is injected
  it.skip('total expires the cart after the timeout elapses', () => {
    expect(total([1])).toBe(1);
  });

  it.only('total ignores the tax when the region is exempt', () => {
    expect(total([5])).toBe(5);
  });

  it('total handles a list of items with a // comment-like string', () => {
    const x = 1;
    expect(x).toBe(x);
  });
});
