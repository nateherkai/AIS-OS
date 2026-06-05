import type { Adapter } from './types'
import { remoteOkAdapter } from './remoteok'
import { remotiveAdapter } from './remotive'
import { wwrAdapter } from './weworkremotely'

export function automatedAdapters(): Adapter[] {
  return [remoteOkAdapter(), remotiveAdapter(), wwrAdapter()]   // hackernews added in Task 8
}
