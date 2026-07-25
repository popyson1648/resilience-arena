import { Button, Chip, Heading, NotificationBar, Text } from 'smarthr-ui'
import styled from 'styled-components'

import { AgentActivity } from './components/AgentActivity'
import { MetricsChart } from './components/MetricsChart'
import { ResultPanel } from './components/ResultPanel'
import { ScenarioPanel } from './components/ScenarioPanel'
import { SystemDiagram } from './components/SystemDiagram'
import { useDemo } from './state/useDemo'

export const App = () => {
  const { state, start, reset } = useDemo()
  const { scenario, runState, stage, maxStageIndex, system, activities, result, error } = state

  return (
    <Page>
      <TopBar role="banner">
        <TitleGroup>
          <Heading type="sectionTitle">
            Resilience Arena
          </Heading>
          <Chip color="orange">シミュレーション環境</Chip>
          <Text size="S" color="TEXT_GREY">
            AIエージェントによる障害対応デモ(実環境は操作しません)
          </Text>
        </TitleGroup>
        <Button size="S" onClick={reset}>
          初期状態へ戻す
        </Button>
      </TopBar>

      {state.connectionLost && (
        <NotificationBar type="error" bold role="alert">
          サーバーとの接続に問題があります。リセットして再実行してください。
        </NotificationBar>
      )}
      {error && (
        <NotificationBar type="error" bold role="alert">
          {`実行エラー(${error.stopped_stage_label} の段階で停止): ${error.message}`}
        </NotificationBar>
      )}

      <Panel>
        <ScenarioPanel
          scenario={scenario}
          runState={runState}
          startedAt={state.startedAt}
          finishedElapsed={result?.elapsed_seconds ?? null}
          onStart={start}
        />
      </Panel>

      <Columns>
        <Panel aria-label="システム状態">
          <PanelHeading>
            <Heading type="blockTitle">
              システム状態
            </Heading>
            {system && <Text size="XS" color="TEXT_GREY">シミュレーション時刻 {system.now}</Text>}
          </PanelHeading>
          {system && (
            <>
              <SystemDiagram system={system} />
              <MetricsChart system={system} />
            </>
          )}
        </Panel>

        <Panel aria-label="エージェント実行">
          <PanelHeading>
            <Heading type="blockTitle">
              AIエージェントの調査と操作
            </Heading>
          </PanelHeading>
          <AgentActivity
            stage={stage}
            maxStageIndex={maxStageIndex}
            activities={activities}
            runState={runState}
          />
        </Panel>
      </Columns>

      {(result || error) && (
        <Panel aria-label="対応結果">
          <PanelHeading>
            <Heading type="blockTitle">
              対応結果
            </Heading>
          </PanelHeading>
          {result ? (
            <ResultPanel result={result} />
          ) : (
            <Text as="p">
              実行エラーのため結果はありません。「デモを開始」からもう一度実行できます。
            </Text>
          )}
        </Panel>
      )}
    </Page>
  )
}

const Page = styled.main`
  max-width: 1280px;
  margin: 0 auto;
  padding: 16px 20px 32px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 100vh;
  background: #f8f7f6;
`

const TopBar = styled.header`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
`

const TitleGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
`

const Panel = styled.section`
  background: #fff;
  border: 1px solid #e5e4e1;
  border-radius: 8px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
`

const PanelHeading = styled.div`
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
`

const Columns = styled.div`
  display: grid;
  grid-template-columns: minmax(0, 11fr) minmax(0, 9fr);
  gap: 12px;
  align-items: stretch;

  @media (max-width: 1000px) {
    grid-template-columns: 1fr;
  }

  & > section:last-child {
    max-height: 560px;
  }
`
