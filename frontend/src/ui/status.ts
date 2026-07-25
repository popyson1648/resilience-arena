import type { ServiceStatus } from '../api/events'

// Color + icon + text together: states must be distinguishable without color alone.
export const SERVICE_STATUS_META: Record<
  ServiceStatus,
  { label: string; icon: string; color: string; bg: string; border: string }
> = {
  healthy: { label: '正常', icon: '✓', color: '#0f6e33', bg: '#e6f4ea', border: '#4bab6e' },
  warning: { label: '警告', icon: '△', color: '#7a5d00', bg: '#fff3c2', border: '#c7a300' },
  down: { label: '障害', icon: '✕', color: '#b3261e', bg: '#fdeceb', border: '#e05252' },
}

export const RUN_STATE_TYPE: Record<
  string,
  'grey' | 'blue' | 'green' | 'red' | 'warning' | 'error'
> = {
  idle: 'grey',
  fault_injected: 'error',
  investigating: 'blue',
  cause_identified: 'blue',
  recovering: 'warning',
  verifying: 'blue',
  recovered: 'green',
  recovery_failed: 'error',
  execution_error: 'error',
}

export const TOOL_LABELS: Record<string, string> = {
  get_metrics: 'メトリクス確認',
  search_logs: 'ログ検索',
  get_deploy_history: 'デプロイ履歴',
  rollback_revision: 'ロールバック',
  check_health: '正常性確認',
}
