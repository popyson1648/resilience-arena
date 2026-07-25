import type { ScenarioInfo, SseEvent } from './events'

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return (await res.json()) as T
}

export const fetchScenario = async (): Promise<ScenarioInfo> =>
  json(await fetch('/api/scenario'))

export const createRun = async (): Promise<{ run_id: string }> =>
  json(await fetch('/api/runs', { method: 'POST' }))

export const fetchRunSnapshot = async (
  runId: string,
): Promise<{ run_id: string; state: string; events: SseEvent[] }> =>
  json(await fetch(`/api/runs/${runId}`))

export const cancelRun = async (runId: string): Promise<void> => {
  await fetch(`/api/runs/${runId}/cancel`, { method: 'POST' })
}

export const openEventStream = (
  runId: string,
  onEvent: (event: SseEvent) => void,
  onError: () => void,
): EventSource => {
  const source = new EventSource(`/api/runs/${runId}/events`)
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data) as SseEvent)
    } catch {
      // ignore malformed frames; the snapshot endpoint recovers state on reconnect
    }
  }
  source.onerror = onError
  return source
}
