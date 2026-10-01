import { describe, it, expect } from 'vitest'
import { tabToText, blankTab, EMPTY, TECH } from '@/design-system/core/tab'

describe('tabToText & tab helpers', () => {
  it('formats an empty column correctly with default string names', () => {
    const cols = [EMPTY()]
    const expected = [
      'e|--|',
      'B|--|',
      'G|--|',
      'D|--|',
      'A|--|',
      'E|--|',
    ].join('\n')
    expect(tabToText(cols)).toBe(expected)
  })

  it('formats blankTab(3) columns', () => {
    const cols = blankTab(3)
    const expected = [
      'e|------|',
      'B|------|',
      'G|------|',
      'D|------|',
      'A|------|',
      'E|------|',
    ].join('\n')
    expect(tabToText(cols)).toBe(expected)
  })

  it('handles multi-character frets and column width padding', () => {
    const cols = [
      ['12', '0', '', '', '', ''],
      ['', '3', '5h7', '', '', ''],
    ]
    const expected = [
      'e|12-----|',
      'B|0--3---|',
      'G|---5h7-|',
      'D|-------|',
      'A|-------|',
      'E|-------|',
    ].join('\n')
    expect(tabToText(cols)).toBe(expected)
  })

  it('renders bar lines correctly', () => {
    const cols: Array<string[] | '|'> = [
      ['0', '', '', '', '', ''],
      '|',
      ['', '1', '', '', '', ''],
    ]
    const expected = [
      'e|0-|--|',
      'B|--|1-|',
      'G|--|--|',
      'D|--|--|',
      'A|--|--|',
      'E|--|--|',
    ].join('\n')
    expect(tabToText(cols)).toBe(expected)
  })

  it('supports custom string tuning names', () => {
    const cols = [EMPTY()]
    const names = ['1', '2', '3', '4', '5', '6']
    const expected = [
      '1|--|',
      '2|--|',
      '3|--|',
      '4|--|',
      '5|--|',
      '6|--|',
    ].join('\n')
    expect(tabToText(cols, names)).toBe(expected)
  })

  it('defines TECH constant matching bundle.js', () => {
    expect(TECH).toBe('hpbrs/\\~xv')
  })
})
