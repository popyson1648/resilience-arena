import { STAGE_ORDER, TERMINAL_STATES } from '../api/events'
import type {
  ErrorPayload,
  ResultPayload,
  RunStateName,
  ScenarioInfo,
  SseEvent,
  StageName,
  SystemSnapshot,
} from '../api/events'

export type Activity = {
  id: number
  tool: string
  reason: string
  args: Record<string, unknown>
  summary: string | null
  blocked: boolean
}

export type DemoState = {
  scenario: ScenarioInfo | null
  runId: string | null
  runState: RunStateName
  stage: StageName | null
  maxStageIndex: number
  system: SystemSnapshot | null
  activities: Activity[]
  result: ResultPayload | null
  error: ErrorPayload | null
  blockedCount: number
  startedAt: number | null
  connectionLost: boolean
}

export const initialDemoState: DemoState = {
  scenario: null,
  runId: null,
  runState: 'idle',
  stage: null,
  maxStageIndex: -1,
  system: null,
  activities: [],
  result: null,
  error: null,
  blockedCount: 0,
  startedAt: null,
  connectionLost: false,
}

export type DemoAction =
  | { type: 'scenario_loaded'; scenario: ScenarioInfo }
  | { type: 'run_started'; runId: string }
  | { type: 'sse_event'; event: SseEvent }
  | { type: 'connection_lost' }
  | { type: 'reset' }

let nextActivityId = 1

export function demoReducer(state: DemoState, action: DemoAction): DemoState {
  switch (action.type) {
    case 'scenario_loaded':
      return {
        ...state,
        scenario: action.scenario,
        system: state.system ?? action.scenario.initial_system,
      }
    case 'run_started':
      return {
        ...initialDemoState,
        scenario: state.scenario,
        system: state.scenario?.initial_system ?? null,
        runId: action.runId,
        startedAt: Date.now(),
      }
    case 'connection_lost':
      // the server closes the stream after a terminal event; that is not a failure
      if (TERMINAL_STATES.includes(state.runState)) return state
      return { ...state, connectionLost: true }
    case 'reset':
      return {
        ...initialDemoState,
        scenario: state.scenario,
        system: state.scenario?.initial_system ?? null,
      }
    case 'sse_event':
      return applyEvent(state, action.event)
  }
}

function applyEvent(state: DemoState, event: SseEvent): DemoState {
  switch (event.type) {
    case 'run_state':
      return { ...state, runState: event.payload.state }
    case 'stage': {
      const index = STAGE_ORDER.indexOf(event.payload.stage)
      return {
        ...state,
        stage: event.payload.stage,
        maxStageIndex: Math.max(state.maxStageIndex, index),
      }
    }
    case 'system_state':
      return { ...state, system: event.payload }
    case 'tool_call':
      return {
        ...state,
        activities: [
          ...state.activities,
          {
            id: nextActivityId++,
            tool: event.payload.tool,
            reason: event.payload.reason,
            args: event.payload.args,
            summary: null,
            blocked: false,
          },
        ],
      }
    case 'tool_result': {
      const activities = [...state.activities]
      for (let i = activities.length - 1; i >= 0; i--) {
        if (activities[i].tool === event.payload.tool && activities[i].summary === null) {
          activities[i] = {
            ...activities[i],
            summary: event.payload.summary,
            blocked: event.payload.blocked,
          }
          break
        }
      }
      return { ...state, activities }
    }
    case 'safety_blocked':
      return { ...state, blockedCount: event.payload.blocked_count }
    case 'result':
      return { ...state, result: event.payload }
    case 'error':
      return { ...state, error: event.payload }
  }
}
