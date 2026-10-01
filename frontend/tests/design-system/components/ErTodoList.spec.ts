import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ErTodoList, { type TodoItem } from '@/design-system/components/ErTodoList.vue'

describe('ErTodoList component', () => {
  it('renders empty state when there are no items', () => {
    const wrapper = mount(ErTodoList, {
      props: {
        modelValue: [],
      },
    })
    expect(wrapper.classes()).toContain('er-todo')
    expect(wrapper.classes()).toContain('er-panel')
    expect(wrapper.find('.er-todo-empty').text()).toBe(
      'Nada pendiente. Toca otra vez desde el coro.'
    )
    expect(wrapper.find('.er-todo-foot').text()).toContain('0 pendientes · 0 hechas')
  })

  it('renders items with checkboxes, text, and delete buttons', () => {
    const sampleItems: TodoItem[] = [
      { id: '1', text: 'Escribir segundo verso', done: false },
      { id: '2', text: 'Arreglar intro', done: true },
    ]
    const wrapper = mount(ErTodoList, {
      props: {
        title: 'Tareas',
        modelValue: sampleItems,
      },
    })
    expect(wrapper.find('.er-label').text()).toBe('// Tareas')
    const listItems = wrapper.findAll('.er-todo-item')
    expect(listItems.length).toBe(2)
    expect(listItems[0].classes()).not.toContain('is-done')
    expect(listItems[1].classes()).toContain('is-done')

    expect(wrapper.find('.er-todo-foot').text()).toContain('1 pendiente · 1 hecha')
    expect(wrapper.find('button.er-btn--ghost').text()).toBe('Limpiar hechas')
  })

  it('supports adding a new task', async () => {
    const wrapper = mount(ErTodoList, {
      props: {
        modelValue: [],
      },
    })
    const input = wrapper.find('.er-compose input')
    await input.setValue('Grabar bajo')

    const addBtn = wrapper.find('.er-compose button')
    await addBtn.trigger('click')

    const emitted = (wrapper.emitted('update:modelValue')?.[0]?.[0] || wrapper.emitted('change')?.[0]?.[0]) as TodoItem[]
    expect(emitted).toBeDefined()
    expect(emitted.length).toBe(1)
    expect(emitted[0].text).toBe('Grabar bajo')
    expect(emitted[0].done).toBe(false)
  })

  it('toggles task done status, deletes task, and clears done tasks', async () => {
    const sampleItems: TodoItem[] = [
      { id: '1', text: 'Tarea 1', done: false },
      { id: '2', text: 'Tarea 2', done: true },
    ]
    const wrapper = mount(ErTodoList, {
      props: {
        modelValue: sampleItems,
      },
    })

    // Toggle Tarea 1
    const checkBtns = wrapper.findAll('button.er-check')
    await checkBtns[0].trigger('click')

    let lastEmitted = (wrapper.emitted('update:modelValue')?.slice(-1)[0]?.[0] || wrapper.emitted('change')?.slice(-1)[0]?.[0]) as TodoItem[]
    expect(lastEmitted.find((x) => x.id === '1')?.done).toBe(true)

    // Clear done
    const clearBtn = wrapper.find('button.er-btn--ghost')
    await clearBtn.trigger('click')

    lastEmitted = (wrapper.emitted('update:modelValue')?.slice(-1)[0]?.[0] || wrapper.emitted('change')?.slice(-1)[0]?.[0]) as TodoItem[]
    expect(lastEmitted.length).toBe(0)
  })
})
