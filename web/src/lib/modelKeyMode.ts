/** How a team's model key reaches formal runs. */
export type ModelKeyMode = 'stored' | 'relay'

/**
 * Not saving the key (the page relay) is the default. Saving it encrypted on the
 * server is an explicit opt-in: only a team that chose it, or saved a key, is in
 * stored mode.
 */
export const DEFAULT_MODEL_KEY_MODE: ModelKeyMode = 'relay'

export function teamModelMode(teamModel: { mode?: string | null } | null | undefined): ModelKeyMode {
  return teamModel?.mode === 'stored' ? 'stored' : DEFAULT_MODEL_KEY_MODE
}
