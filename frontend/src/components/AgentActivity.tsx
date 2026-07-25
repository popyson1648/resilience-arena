import { useEffect, useRef } from 'react'
import { Base, Chip, Loader, Stepper, Text } from 'smarthr-ui'
import styled from 'styled-components'

import { STAGE_LABELS, STAGE_ORDER, TERMINAL_STATES } from '../api/events'
import type { RunStateName, StageName } from '../api/events'
import type { Activity } from '../state/demoReducer'
import { TOOL_LABELS } from '../ui/status'

type Props = {
  stage: StageName | null
  maxStageIndex: number
  activities: Activity[]
  runState: RunStateName
}

export const AgentActivity = ({ stage, maxStageIndex, activities, runState }: Props) => {
  const running = runState !== 'idle' && !TERMINAL_STATES.includes(runState)
  const feedRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: 'smooth' })
  }, [activities.length, runState])

  const activeIndex = stage ? STAGE_ORDER.indexOf(stage) : -1
  const steps = STAGE_ORDER.map((name, index) => ({
    label: STAGE_LABELS[name],
    status: index < maxStageIndex || (index <= maxStageIndex && !running && maxStageIndex >= 0)
      ? ('completed' as const)
      : undefined,
  }))

  return (
    <Layout>
      <StepperColumn>
        <Stepper type="vertical" steps={steps} activeIndex={activeIndex} />
      </StepperColumn>
      <Feed ref={feedRef} aria-live="polite" aria-label="エージェントの調査と操作の記録">
        {activities.length === 0 && (
          <Text as="p" size="S" color="TEXT_GREY">
            {running ? 'エージェントが状況を確認しています…' : 'デモを開始すると、AIエージェントの調査と操作がここに表示されます。'}
          </Text>
        )}
        {activities.map((activity) => (
          <ActivityCard key={activity.id} $blocked={activity.blocked}>
            <CardHeader>
              <Chip color={activity.blocked ? 'red' : activity.tool === 'rollback_revision' ? 'orange' : 'blue'}>
                {TOOL_LABELS[activity.tool] ?? activity.tool}
              </Chip>
              <Text size="XS" color="TEXT_GREY">
                {formatArgs(activity.args)}
              </Text>
            </CardHeader>
            {activity.reason && (
              <Text as="p" size="S">
                {activity.reason}
              </Text>
            )}
            {activity.summary === null ? (
              <Loader size="S" alt="実行中" />
            ) : (
              <Observation $blocked={activity.blocked}>
                <Text size="S" weight={activity.blocked ? 'bold' : undefined}>
                  {activity.blocked ? '拒否: ' : '観測: '}
                  {activity.summary}
                </Text>
              </Observation>
            )}
          </ActivityCard>
        ))}
        {running && activities.length > 0 && activities[activities.length - 1].summary !== null && (
          <ThinkingRow>
            <Loader size="S" alt="" />
            <Text size="S" color="TEXT_GREY">
              次の操作を検討中…
            </Text>
          </ThinkingRow>
        )}
      </Feed>
    </Layout>
  )
}

const formatArgs = (args: Record<string, unknown>): string =>
  Object.entries(args)
    .map(([key, value]) => `${key}=${String(value)}`)
    .join(' ')

const Layout = styled.div`
  display: grid;
  grid-template-columns: 176px 1fr;
  gap: 16px;
  min-height: 0;
  height: 100%;
`

const StepperColumn = styled.div`
  overflow-y: auto;
`

const Feed = styled.div`
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-right: 4px;
  min-height: 0;
`

const ActivityCard = styled(Base)<{ $blocked: boolean }>`
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  border-left: 4px solid ${({ $blocked }) => ($blocked ? '#b3261e' : '#3970b8')};
`

const CardHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
`

const Observation = styled.div<{ $blocked: boolean }>`
  background: ${({ $blocked }) => ($blocked ? '#fdeceb' : '#f3f6fa')};
  border-radius: 6px;
  padding: 6px 10px;
`

const ThinkingRow = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 2px;
`
