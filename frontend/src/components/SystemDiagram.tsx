import type { SystemSnapshot } from '../api/events'
import { SERVICE_STATUS_META } from '../ui/status'

const NODE_W = 168
const NODE_H = 92
const NODE_Y = 24
const XS = [12, 216, 420, 624]

// Plain-text badges: emoji glyphs are not guaranteed to render inside SVG everywhere.
const KIND_BADGES: Record<string, string> = {
  client: 'C',
  load_balancer: 'LB',
  application: 'AP',
  database: 'DB',
}

type Props = { system: SystemSnapshot }

export const SystemDiagram = ({ system }: Props) => {
  const services = system.services
  const byName = Object.fromEntries(services.map((s) => [s.name, s]))
  const appDown = services.some((s) => s.kind === 'application' && s.status !== 'healthy')

  return (
    <svg
      viewBox="0 0 804 140"
      role="img"
      aria-label={`システム構成図: ${services.map((s) => `${s.label}は${SERVICE_STATUS_META[s.status].label}`).join('、')}`}
      style={{ width: '100%', height: 'auto', display: 'block' }}
    >
      <defs>
        <marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="#5c5c5c" />
        </marker>
        <marker id="arrow-bad" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L8,4 L0,8 z" fill="#b3261e" />
        </marker>
      </defs>

      {XS.slice(0, -1).map((x, i) => {
        const impacted = appDown && i >= 0 && i <= 1
        const dbEdge = i === 2
        const stroke = impacted ? '#b3261e' : '#5c5c5c'
        return (
          <g key={i}>
            <line
              x1={x + NODE_W + 4}
              y1={NODE_Y + NODE_H / 2}
              x2={XS[i + 1] - 6}
              y2={NODE_Y + NODE_H / 2}
              stroke={stroke}
              strokeWidth={impacted ? 3 : 2}
              strokeDasharray={impacted ? '7 5' : dbEdge && appDown ? '2 4' : undefined}
              markerEnd={impacted ? 'url(#arrow-bad)' : 'url(#arrow)'}
            >
              {impacted && (
                <animate attributeName="stroke-dashoffset" from="24" to="0" dur="1s" repeatCount="indefinite" />
              )}
            </line>
            {impacted && (
              <text
                x={(x + NODE_W + XS[i + 1]) / 2}
                y={NODE_Y + NODE_H / 2 - 10}
                textAnchor="middle"
                fontSize="13"
                fill="#b3261e"
              >
                エラー応答
              </text>
            )}
          </g>
        )
      })}

      {services.map((service, i) => {
        const meta = SERVICE_STATUS_META[service.status]
        const x = XS[i]
        return (
          <g key={service.name}>
            <rect
              x={x}
              y={NODE_Y}
              width={NODE_W}
              height={NODE_H}
              rx={10}
              fill={meta.bg}
              stroke={meta.border}
              strokeWidth={2.5}
            />
            <circle cx={x + 26} cy={NODE_Y + 23} r={13} fill="#fff" stroke={meta.border} />
            <text
              x={x + 26}
              y={NODE_Y + 27}
              textAnchor="middle"
              fontSize="11"
              fontWeight="bold"
              fill={meta.color}
            >
              {KIND_BADGES[service.kind]}
            </text>
            <text x={x + 46} y={NODE_Y + 28} fontSize="15" fontWeight="bold" fill="#23221f">
              {service.label}
            </text>
            <text x={x + 14} y={NODE_Y + 50} fontSize="12" fill="#706d65">
              {service.name}
              {service.kind === 'application' ? ` (${system.current_revision})` : ''}
            </text>
            <g>
              <rect x={x + 12} y={NODE_Y + 60} width={72} height={22} rx={11} fill="#fff" stroke={meta.border} />
              <text x={x + 48} y={NODE_Y + 76} textAnchor="middle" fontSize="13" fontWeight="bold" fill={meta.color}>
                {meta.icon} {meta.label}
              </text>
            </g>
          </g>
        )
      })}
      {byName['orders-db'] && appDown && (
        <text x={XS[3] + NODE_W / 2} y={NODE_Y + NODE_H + 18} textAnchor="middle" fontSize="12" fill="#706d65">
          DB は正常稼働中
        </text>
      )}
    </svg>
  )
}
