import '@testing-library/jest-dom'
import { jest } from '@jest/globals'
import { TextDecoder, TextEncoder } from 'util'

Object.defineProperty(globalThis, 'TextEncoder', {
  configurable: true,
  value: TextEncoder,
})

Object.defineProperty(globalThis, 'TextDecoder', {
  configurable: true,
  value: TextDecoder,
})

Object.defineProperty(window.HTMLElement.prototype, 'scrollIntoView', {
  configurable: true,
  value: jest.fn(),
})
