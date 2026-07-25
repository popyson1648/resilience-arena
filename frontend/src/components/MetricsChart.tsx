import type { SystemSnapshot } from '../api/events'

const W = 804
const H = 190
const PAD_L = 46
const PAD_R = 14
const PAD_T = 18
const PAD_B = 34
const Y_MAX = 50 // error-rate axis (%)

type Props = { system: SystemSnapshot }

export const MetricsChart = ({ system }: Props) => {
  const points = system.app_metrics.points
  if (points.length < 2) return null
  const summary = system.app_metrics.summary

  const x = (i: number) => PAD_L + (i * (W - PAD_L - PAD_R)) / (points.length - 1)
  const y = (v: number) => PAD_T + (1 - Math.min(v, Y_MAX) / Y_MAX) * (H - PAD_T - PAD_B)

  const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(p.error_rate_pct)}`).join(' ')
  const area = `${line} L${x(points.length - 1)},${y(0)} L${x(0)},${y(0)} Z`
  const deployIndex = points.findIndex((p) => p.time === system.deploy_marker)
  const current = points[points.length - 1]
  const currentColor = current.error_rate_pct > 5 ? '#b3261e' : '#0f6e33'

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      role="img"
      aria-label={`決済サービスのエラー率推移。現在 ${current.error_rate_pct}%`}
      style={{ width: '100%', height: 'auto', display: 'block' }}
    >
      {[0, 10, 20, 30, 40, 50].map((v) => (
        <g key={v}>
          <line x1={PAD_L} y1={y(v)} x2={W - PAD_R} y2={y(v)} stroke="#e5e4e1" strokeWidth={1} />
          <text x={PAD_L - 8} y={y(v) + 4} textAnchor="end" fontSize="11" fill="#706d65">
            {v}%
          </text>
        </g>
      ))}

      <path d={area} fill="#e0526820" />
      <path d={line} fill="none" stroke={currentColor} strokeWidth={2.5} />

      <line
        x1={x(0)}
        y1={y(summary.baseline_error_rate_pct)}
        x2={x(points.length - 1)}
        y2={y(summary.baseline_error_rate_pct)}
        stroke="#0f6e33"
        strokeDasharray="3 4"
        strokeWidth={1.5}
      />
      <text x={PAD_L + 6} y={y(summary.baseline_error_rate_pct) - 6} fontSize="11" fill="#0f6e33">
        平常時 {summary.baseline_error_rate_pct}%
      </text>

      {deployIndex >= 0 && (
        <g>
          <line x1={x(deployIndex)} y1={PAD_T - 4} x2={x(deployIndex)} y2={y(0)} stroke="#5a44c0" strokeWidth={2} strokeDasharray="5 4" />
          <text x={x(deployIndex) + 5} y={PAD_T + 8} fontSize="12" fontWeight="bold" fill="#5a44c0">
            ▼ rev-002 デプロイ ({system.deploy_marker})
          </text>
        </g>
      )}

      {points.map((p, i) =>
        i % 5 === 0 || i === points.length - 1 ? (
          <text key={p.time} x={x(i)} y={H - 10} textAnchor="middle" fontSize="11" fill="#706d65">
            {p.time}
          </text>
        ) : null,
      )}

      <circle cx={x(points.length - 1)} cy={y(current.error_rate_pct)} r={4.5} fill={currentColor} />
      <text
        x={x(points.length - 1) - 8}
        y={y(current.error_rate_pct) - 10}
        textAnchor="end"
        fontSize="14"
        fontWeight="bold"
        fill={currentColor}
      >
        エラー率 {current.error_rate_pct}%
      </text>
    </svg>
  )
}
