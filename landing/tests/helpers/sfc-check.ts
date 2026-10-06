import { parse } from '@vue/compiler-sfc'

export function extractSfcTextsAndAttributes(sfcSource: string): string[] {
  const { descriptor } = parse(sfcSource)
  if (!descriptor.template || !descriptor.template.ast) {
    return []
  }

  const items: string[] = []

  function walk(node: any) {
    if (!node) return

    // NodeTypes.TEXT === 2
    if (node.type === 2 && typeof node.content === 'string') {
      const trimmed = node.content.trim()
      if (trimmed.length > 0) {
        items.push(trimmed)
      }
    }

    // NodeTypes.ATTRIBUTE === 6 (static attributes)
    if (Array.isArray(node.props)) {
      for (const prop of node.props) {
        if (prop.type === 6 && prop.value && typeof prop.value.content === 'string') {
          items.push(prop.value.content)
        }
      }
    }

    if (Array.isArray(node.children)) {
      for (const child of node.children) {
        walk(child)
      }
    }
  }

  walk(descriptor.template.ast)
  return items
}

export function checkCopyViolations(sfcSource: string, filePath: string) {
  const emojiRegex = /\p{Extended_Pictographic}/u
  const violations: { file: string; reason: string; line: string }[] = []
  const texts = extractSfcTextsAndAttributes(sfcSource)

  for (const text of texts) {
    if (text.includes('!')) {
      violations.push({
        file: filePath,
        reason: 'exclamation mark in copy',
        line: text,
      })
    }
    if (emojiRegex.test(text)) {
      violations.push({
        file: filePath,
        reason: 'emoji in copy',
        line: text,
      })
    }
  }

  return violations
}
