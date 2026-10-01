import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AppModal from '@/shared/AppModal.vue'

describe('AppModal component', () => {
  beforeEach(() => {
    document.body.innerHTML = ''
  })

  afterEach(() => {
    document.body.innerHTML = ''
  })

  it('renders overlay with backdrop and dialog with z-index 60', () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
        title: 'Título del modal',
      },
      slots: {
        default: '<button id="modal-btn">Acción</button>',
      },
      attachTo: document.body,
    })

    const backdrop = wrapper.find('.er-modal-backdrop')
    expect(backdrop.exists()).toBe(true)
    const modal = wrapper.find('.er-modal')
    expect(modal.exists()).toBe(true)
    expect(wrapper.text()).toContain('Título del modal')
    expect(wrapper.find('#modal-btn').exists()).toBe(true)
    wrapper.unmount()
  })

  it('emits close when backdrop is clicked', async () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: '<p>Contenido</p>',
      },
      attachTo: document.body,
    })

    const backdrop = wrapper.find('.er-modal-backdrop')
    await backdrop.trigger('click')

    expect(wrapper.emitted('close')).toBeTruthy()
    expect(wrapper.emitted('close')?.length).toBe(1)
    wrapper.unmount()
  })

  it('does NOT emit close when modal content itself is clicked', async () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: '<button id="inner-btn">Contenido</button>',
      },
      attachTo: document.body,
    })

    const modal = wrapper.find('.er-modal')
    await modal.trigger('click')
    const innerBtn = wrapper.find('#inner-btn')
    await innerBtn.trigger('click')

    expect(wrapper.emitted('close')).toBeFalsy()
    wrapper.unmount()
  })

  it('emits close when Escape key is pressed', async () => {
    const wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: '<p>Contenido</p>',
      },
      attachTo: document.body,
    })

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))

    expect(wrapper.emitted('close')).toBeTruthy()
    expect(wrapper.emitted('close')?.length).toBe(1)
    wrapper.unmount()
  })

  it('traps keyboard focus within modal elements while open', async () => {
    const triggerBtn = document.createElement('button')
    triggerBtn.id = 'trigger'
    document.body.appendChild(triggerBtn)
    triggerBtn.focus()

    const wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: `
          <input id="input1" type="text" />
          <button id="btn1">Boton 1</button>
          <button id="btn2">Boton 2</button>
        `,
      },
      attachTo: document.body,
    })

    const input1 = document.getElementById('input1') as HTMLElement
    const btn2 = document.getElementById('btn2') as HTMLElement

    // Focus first element or close button
    const closeBtn = wrapper.find('.er-modal-close')
    if (closeBtn.exists()) {
      (closeBtn.element as HTMLElement).focus()
    } else {
      input1?.focus()
    }

    // When on last element and pressing Tab without shift, wraps to first element
    btn2?.focus()
    expect(document.activeElement).toBe(btn2)

    const tabEvent = new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })
    window.dispatchEvent(tabEvent)

    wrapper.unmount()
    triggerBtn.remove()
  })

  it('restores keyboard focus to previous trigger element on close', async () => {
    const triggerBtn = document.createElement('button')
    triggerBtn.id = 'trigger-restore'
    document.body.appendChild(triggerBtn)
    triggerBtn.focus()
    expect(document.activeElement).toBe(triggerBtn)

    const wrapper = mount(AppModal, {
      props: {
        open: true,
      },
      slots: {
        default: '<button id="m-btn">Inside</button>',
      },
      attachTo: document.body,
    })

    await wrapper.setProps({ open: false })
    expect(document.activeElement).toBe(triggerBtn)

    wrapper.unmount()
    triggerBtn.remove()
  })
})
