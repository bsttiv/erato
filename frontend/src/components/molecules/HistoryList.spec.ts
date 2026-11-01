// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import HistoryList from './HistoryList.vue'

const author = { display_name: 'Ana', username: 'ana' }
const render = (item: Record<string, unknown>) => mount(HistoryList, {
  props: { items: [{ version: 3, author, created_at: '2026-10-31T12:00:00Z', ...item }], canRestore: true },
})

describe('HistoryList — tests_md/propuesta-landing-app-2026-10-31.md', () => {
  it('HIS-014 shows the author, summary, date and actions', () => {
    const wrapper = render({ summary: 'editó la letra de Coro' })
    expect(wrapper.text()).toContain('Ana editó la letra de Coro')
    expect(wrapper.text()).toContain(new Date('2026-10-31T12:00:00Z').toLocaleString('es'))
    expect(wrapper.text()).not.toContain('Versión 3')
    expect(wrapper.findAll('button').map(button => button.text())).toEqual(['Ver', 'Restaurar'])
  })
  it('HIS-015 falls back to the version without a summary', () => {
    expect(render({ summary: null }).text()).toContain('Ana · Versión 3')
  })
})
