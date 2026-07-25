import { useCallback, useEffect, useReducer, useRef } from 'react'

import { cancelRun, createRun, fetchScenario, openEventStream } from '../api/client'
import { TERMINAL_STATES } from '../api/events'
import { demoReducer, initialDemoState } from './demoReducer'

export function useDemo() {
  const [state, dispatch] = useReducer(demoReducer, initialDemoState)
  const sourceRef = useRef<EventSource | null>(null)
  const stateRef = useRef(state)

  useEffect(() => {
    stateRef.current = state
  }, [state])

  useEffect(() => {
    let cancelled = false
    fetchScenario()
      .then((scenario) => {
        if (!cancelled) dispatch({ type: 'scenario_loaded', scenario })
      })
      .catch(() => {
        if (!cancelled) dispatch({ type: 'connection_lost' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const closeStream = useCallback(() => {
    sourceRef.current?.close()
    sourceRef.current = null
  }, [])

  // close the SSE connection once the run reaches a terminal state
  useEffect(() => {
    if (TERMINAL_STATES.includes(state.runState)) closeStream()
  }, [state.runState, closeStream])

  useEffect(() => closeStream, [closeStream])

  const start = useCallback(async () => {
    closeStream()
    try {
      const { run_id } = await createRun()
      dispatch({ type: 'run_started', runId: run_id })
      sourceRef.current = openEventStream(
        run_id,
        (event) => dispatch({ type: 'sse_event', event }),
        () => {
          // EventSource retries automatically; only report when the run cannot finish
          if (!TERMINAL_STATES.includes(stateRef.current.runState)) {
            dispatch({ type: 'connection_lost' })
          }
        },
      )
    } catch {
      dispatch({ type: 'connection_lost' })
    }
  }, [closeStream])

  const reset = useCallback(() => {
    const { runId, runState } = stateRef.current
    closeStream()
    if (runId && !TERMINAL_STATES.includes(runState)) {
      void cancelRun(runId).catch(() => undefined)
    }
    dispatch({ type: 'reset' })
  }, [closeStream])

  return { state, start, reset }
}
