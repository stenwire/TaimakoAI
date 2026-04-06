import { cn } from '@/lib/utils';

describe('cn utility', () => {
  it('merges multiple class strings', () => {
    expect(cn('foo', 'bar')).toBe('foo bar');
  });

  it('ignores false values', () => {
    expect(cn('foo', false && 'bar')).toBe('foo');
  });

  it('ignores null values', () => {
    expect(cn('foo', null)).toBe('foo');
  });

  it('ignores undefined values', () => {
    expect(cn('foo', undefined)).toBe('foo');
  });

  it('deduplicates conflicting tailwind classes (last wins)', () => {
    expect(cn('p-4', 'p-2')).toBe('p-2');
  });

  it('deduplicates conflicting tailwind color classes', () => {
    expect(cn('text-red-500', 'text-blue-500')).toBe('text-blue-500');
  });

  it('returns empty string for no input', () => {
    expect(cn()).toBe('');
  });

  it('returns empty string for all falsy inputs', () => {
    expect(cn(false, null, undefined)).toBe('');
  });

  it('handles conditional object syntax', () => {
    expect(cn({ 'bg-red-500': true, 'bg-blue-500': false })).toBe('bg-red-500');
  });
});
