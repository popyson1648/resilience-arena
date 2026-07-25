import { DefinitionList, DefinitionListItem, ResponseMessage, Text } from 'smarthr-ui'
import styled from 'styled-components'

import type { ResultPayload } from '../api/events'

type Props = { result: ResultPayload }

export const ResultPanel = ({ result }: Props) => (
  <Wrapper>
    <Verdict>
      <ResponseMessage status={result.success ? 'success' : 'error'} size="M">
        <Text weight="bold" size="M">
          {result.success ? '復旧完了 — システムは正常状態に戻りました' : '復旧失敗 — 対応を完了できませんでした'}
        </Text>
      </ResponseMessage>
      <Text as="p" size="S" color="TEXT_GREY">
        {result.verification_summary}
      </Text>
    </Verdict>
    <DefinitionList>
      <DefinitionListItem term="根本原因(エージェント報告)" fullWidth>
        <Summary>{result.root_cause_summary}</Summary>
      </DefinitionListItem>
      <DefinitionListItem term="実行した復旧操作">{result.recovery_action}</DefinitionListItem>
      <DefinitionListItem term="復旧までの経過時間">{result.elapsed_seconds} 秒</DefinitionListItem>
      <DefinitionListItem term="使用したツール数">{result.tool_call_count} 回</DefinitionListItem>
      <DefinitionListItem term="復旧後の検証">
        {result.verified ? '実施(check_health)' : '未実施'}
      </DefinitionListItem>
      <DefinitionListItem term="安全上拒否された操作">
        {result.safety_blocked_count} 件
      </DefinitionListItem>
    </DefinitionList>
  </Wrapper>
)

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`

const Verdict = styled.div`
  display: flex;
  flex-direction: column;
  gap: 4px;
`

const Summary = styled.span`
  white-space: pre-wrap;
`
