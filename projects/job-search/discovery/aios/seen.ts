import { readFileSync, writeFileSync, existsSync } from 'node:fs'

export function loadSeen(path: string): Set<string> {
  if (!existsSync(path)) return new Set()
  try { return new Set(JSON.parse(readFileSync(path, 'utf8')) as string[]) }
  catch { return new Set() }
}

export function saveSeen(path: string, ids: Set<string>): void {
  writeFileSync(path, JSON.stringify([...ids], null, 2))
}
