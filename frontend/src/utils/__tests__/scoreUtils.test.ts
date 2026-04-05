import { describe, it, expect } from 'vitest'
import { getScoreLevel, getScoreColor, getScoreEmoji } from '@/types/index'

describe('getScoreLevel', () => {
  it('returns high for scores 70 and above', () => {
    expect(getScoreLevel(70)).toBe('high')
    expect(getScoreLevel(100)).toBe('high')
    expect(getScoreLevel(85)).toBe('high')
  })

  it('returns medium for scores 40–69', () => {
    expect(getScoreLevel(40)).toBe('medium')
    expect(getScoreLevel(69)).toBe('medium')
    expect(getScoreLevel(55)).toBe('medium')
  })

  it('returns low for scores below 40', () => {
    expect(getScoreLevel(0)).toBe('low')
    expect(getScoreLevel(39)).toBe('low')
  })
})

describe('getScoreEmoji', () => {
  it('returns checkmark for scores 80 and above', () => {
    expect(getScoreEmoji(80)).toBe('✅')
    expect(getScoreEmoji(100)).toBe('✅')
    expect(getScoreEmoji(95)).toBe('✅')
  })

  it('returns warning for scores 60–79', () => {
    expect(getScoreEmoji(60)).toBe('⚠️')
    expect(getScoreEmoji(79)).toBe('⚠️')
    expect(getScoreEmoji(70)).toBe('⚠️')
  })

  it('returns cross for scores below 60', () => {
    expect(getScoreEmoji(0)).toBe('❌')
    expect(getScoreEmoji(59)).toBe('❌')
    expect(getScoreEmoji(20)).toBe('❌')
  })
})

describe('getScoreColor', () => {
  it('returns green color for scores 70 and above', () => {
    expect(getScoreColor(70)).toBe('text-green-600')
    expect(getScoreColor(100)).toBe('text-green-600')
  })

  it('returns yellow color for scores 40–69', () => {
    expect(getScoreColor(40)).toBe('text-yellow-600')
    expect(getScoreColor(69)).toBe('text-yellow-600')
  })

  it('returns red color for scores below 40', () => {
    expect(getScoreColor(0)).toBe('text-red-600')
    expect(getScoreColor(39)).toBe('text-red-600')
  })

  it('returns a string for any valid score', () => {
    expect(typeof getScoreColor(80)).toBe('string')
    expect(typeof getScoreColor(50)).toBe('string')
    expect(typeof getScoreColor(20)).toBe('string')
  })

  it('returns different colors for different levels', () => {
    expect(getScoreColor(80)).not.toBe(getScoreColor(20))
  })
})
