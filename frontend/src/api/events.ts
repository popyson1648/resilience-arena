// SSE event types. Mirror of backend/app/run/events.py — keep in sync by hand.

export type RunStateName =
  | 'idle'
  | 'fault_injected'
  | 'investigating'
  | 'cause_identified'
  | 'recovering'
  | 'verifying'
  | 'recovered'
  | 'recovery_failed'
  | 'execution_error'

export type StageName =
  | 'situation'
  | 'planning'
  | 'metrics'
  | 'logs'
  | 'deploys'
  | 'cause'
  | 'recovery'
  | 'verify'
  | 'done'

export type ServiceStatus = 'healthy' | 'warning' | 'down'

export type ServiceInfo = {
  name: string
  kind: 'client' | 'load_balancer' | 'application' | 'database'
  label: string
  status: ServiceStatus
}

export type MetricPoint = {
  time: string
  requests_per_min: number
  error_rate_pct: number
  latency_p95_ms: number
}

export type SystemSnapshot = {
  phase: 'healthy' | 'faulted' | 'recovered'
  now: string
  current_revision: string
  services: ServiceInfo[]
  app_metrics: {
    points: MetricPoint[]
    summary: {
      current_error_rate_pct: number
      baseline_error_rate_pct: number
      anomaly_started_at: string | null
    }
  }
  deploy_marker: string
}

export type ResultPayload = {
  success: boolean
  final_state: RunStateName
  root_cause_summary: string
  recovery_action: string
  verified: boolean
  verification_summary: string
  elapsed_seconds: number
  tool_call_count: number
  safety_blocked_count: number
}

export type ErrorPayload = {
  message: string
  stopped_stage_label: string
}

export type SseEvent =
  | { type: 'run_state'; payload: { state: RunStateName; label: string } }
  | { type: 'stage'; payload: { stage: StageName; label: string } }
  | { type: 'system_state'; payload: SystemSnapshot }
  | {
      type: 'tool_call'
      payload: { tool: string; args: Record<string, unknown>; reason: string }
    }
  | { type: 'tool_result'; payload: { tool: string; summary: string; blocked: boolean } }
  | { type: 'safety_blocked'; payload: { tool: string; reason: string; blocked_count: number } }
  | { type: 'result'; payload: ResultPayload }
  | { type: 'error'; payload: ErrorPayload }

export type ScenarioInfo = {
  id: string
  name: string
  description: string
  initial_system: SystemSnapshot
}

export const RUN_STATE_LABELS: Record<RunStateName, string> = {
  idle: '待機中',
  fault_injected: '障害発生',
  investigating: '調査中',
  cause_identified: '原因特定',
  recovering: '復旧操作中',
  verifying: '検証中',
  recovered: '復旧完了',
  recovery_failed: '復旧失敗',
  execution_error: '実行エラー',
}

export const STAGE_ORDER: StageName[] = [
  'situation',
  'planning',
  'metrics',
  'logs',
  'deploys',
  'cause',
  'recovery',
  'verify',
  'done',
]

export const STAGE_LABELS: Record<StageName, string> = {
  situation: '状況把握',
  planning: '調査計画',
  metrics: 'メトリクス確認',
  logs: 'ログ調査',
  deploys: 'デプロイ履歴確認',
  cause: '原因候補の決定',
  recovery: '復旧操作',
  verify: '復旧結果の検証',
  done: '終了判定',
}

export const TERMINAL_STATES: RunStateName[] = ['recovered', 'recovery_failed', 'execution_error']
