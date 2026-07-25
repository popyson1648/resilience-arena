import { useEffect, useState } from 'react'
import { Button, StatusLabel, Text } from 'smarthr-ui'
import styled from 'styled-components'

import { RUN_STATE_LABELS, TERMINAL_STATES } from '../api/events'
import type { RunStateName, ScenarioInfo } from '../api/events'
import { RUN_STATE_TYPE } from '../ui/status'

type Props = {
  scenario: ScenarioInfo | null
  runState: RunStateName
  startedAt: number | null
  finishedElapsed: number | null
  onStart: () => void
}

export const ScenarioPanel = ({ scenario, runState, startedAt, finishedElapsed, onStart }: Props) => {
  const running = runState !== 'idle' && !TERMINAL_STATES.includes(runState)
  const elapsed = useElapsed(running, startedAt)
  const shown = finishedElapsed ?? (running ? elapsed : null)

  return (
    <Row>
      <div>
        <Text as="p" weight="bold" size="M">
          シナリオ: {scenario?.name ?? '読み込み中…'}
        </Text>
        <Text as="p" size="S" color="TEXT_GREY">
          {scenario?.description ?? ''}
        </Text>
      </div>
      <Controls>
        {shown !== null && (
          <Text size="M" weight="bold" as="span">
            経過時間 {shown.toFixed(0)} 秒
          </Text>
        )}
        <StatusLabel type={RUN_STATE_TYPE[runState] ?? 'grey'} bold>
          {RUN_STATE_LABELS[runState]}
        </StatusLabel>
        <Button variant="primary" onClick={onStart} disabled={running || !scenario}>
          {runState === 'idle' ? 'デモを開始' : running ? '実行中…' : 'もう一度実行'}
        </Button>
      </Controls>
    </Row>
  )
}

function useElapsed(running: boolean, startedAt: number | null): number {
  const [elapsed, setElapsed] = useState<{ at: number; value: number } | null>(null)
  useEffect(() => {
    if (!running || startedAt === null) return
    const update = () =>
      setElapsed({ at: startedAt, value: Math.max(0, (Date.now() - startedAt) / 1000) })
    const timer = window.setInterval(update, 250)
    return () => window.clearInterval(timer)
  }, [running, startedAt])
  // ignore values left over from a previous run
  return running && elapsed && elapsed.at === startedAt ? elapsed.value : 0
}

const Row = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
`

const Controls = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`
