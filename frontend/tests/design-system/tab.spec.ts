import { describe, it, expect } from 'vitest'
import {
  tabToText,
  blankTab,
  EMPTY,
  TECH,
  newTabId,
  newTabEntry,
  type TabEntry,
} from '@/design-system/core/tab'

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

  it('newTabId generates unique non-empty identifiers', () => {
    const id1 = newTabId()
    const id2 = newTabId()
    expect(typeof id1).toBe('string')
    expect(id1.length).toBeGreaterThan(0)
    expect(id1).not.toBe(id2)
  })

  it('newTabEntry creates TabEntry with blank columns and default 6 strings', () => {
    const entry: TabEntry = newTabEntry('Intro', 6)
    expect(entry.title).toBe('Intro')
    expect(entry.strings).toBe(6)
    expect(Array.isArray(entry.columns)).toBe(true)
    expect(entry.columns.length).toBe(16)
    expect(entry.columns[0]).toEqual(['', '', '', '', '', ''])
    expect(typeof entry.id).toBe('string')
    expect(entry.id.length).toBeGreaterThan(0)
  })

  it('newTabEntry supports numeric index for default title', () => {
    const entry = newTabEntry(0)
    expect(entry.title).toBe('Tablatura 1')
    expect(entry.strings).toBe(6)
  })
})
