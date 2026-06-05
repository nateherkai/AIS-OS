import type { Adapter } from './types'
import { remoteOkAdapter } from './remoteok'

export function automatedAdapters(): Adapter[] {
  return [remoteOkAdapter()]   // remotive, weworkremotely, hackernews added in Tasks 7–8
}
