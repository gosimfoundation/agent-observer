/** Complete-project evaluation rules shown on the project and records pages. The database enforces them. */
export type EvaluationQuota = { phase_id: string; daily_batches: number; used: number; remaining: number; resets_at?: string }
type Batch = { revision_id?: string | null; phase_id?: string; status: string; quota_refunded?: boolean }
type Revision = { id: string; status: string; archived_at?: string | null; source_kind?: string; source_location?: string; created_at?: string }
type Project = { title: string; observer_revisions: Revision[] }

/** Earlier evaluations of this version in this phase that used a daily evaluation. */
export function countedEvaluations(batches: Batch[] | null | undefined, revisionId: string, phaseId: string): number {
  return (batches ?? []).filter(b => b.revision_id === revisionId && b.phase_id === phaseId && !b.quota_refunded).length
}

/** A version the team has not evaluated can be withdrawn, except while its preparation job runs. */
export function canWithdraw(revision: Revision, batches: Batch[] | null | undefined): boolean {
  return !revision.archived_at && ['queued', 'reviewable', 'failed', 'approved'].includes(revision.status)
    && !(batches ?? []).some(b => b.revision_id === revision.id)
}

/** Withdrawn versions are hidden unless asked for; a project without visible versions is hidden too. */
export function visibleProjects<P extends Project>(projects: P[] | null | undefined, showWithdrawn: boolean): P[] {
  return (projects ?? []).map(p => ({ ...p, observer_revisions: p.observer_revisions.filter(r => showWithdrawn || !r.archived_at) }))
    .filter(p => p.observer_revisions.length)
}

export function withdrawnCount(projects: Project[] | null | undefined): number {
  return (projects ?? []).reduce((n, p) => n + p.observer_revisions.filter(r => r.archived_at).length, 0)
}

const repository = (url: string) => url.trim().toLowerCase().replace(/\/+$/, '').replace(/\.git$/, '')

/** The same project (title and repository, or title for a ZIP) was submitted in the last few minutes. */
export function recentDuplicate(projects: Project[] | null | undefined, title: string, url: string | null, now = Date.now(), windowMs = 10 * 60_000): boolean {
  return (projects ?? []).some(p => p.title.trim() === title.trim() && p.observer_revisions.some(r =>
    !r.archived_at && r.created_at && now - Date.parse(r.created_at) < windowMs
    && (url === null ? r.source_kind === 'zip' : r.source_kind === 'repository' && repository(r.source_location ?? '') === repository(url))))
}
