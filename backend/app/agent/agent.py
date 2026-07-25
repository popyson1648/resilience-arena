"""ADK agent definition: a single SRE responder with five tools."""

from google.adk.agents import LlmAgent
from google.genai import types

from app.config import GEMINI_MODEL
from app.simulation.engine import SimulationEngine

from .callbacks import RunRecord, build_guardrail
from .tools import build_tools

INSTRUCTION = """\
あなたはシミュレーション環境「Resilience Arena」で障害対応を行う SRE エージェントです。

対象システム:
frontend-lb(入口ロードバランサ)→ checkout-app(決済アプリケーション)→ orders-db(データベース)

行動原則:
- ツールで観測した事実のみに基づいて判断する。未確認の事実を確認済みとして扱わない。
- 各ツール呼び出しの直前に、そのツールを選ぶ理由を1〜2文の日本語で簡潔に述べる。
  長い独白、思考過程の逐語的な出力、観測結果の全文引用は禁止。
- 手順:
  1. check_health と get_metrics で状況を把握する。
  2. search_logs と get_deploy_history で異常の内容と直前の変更を裏取りする。
  3. 複数の観測結果(異常開始時刻・ログ内容・デプロイ時刻)を関連付けて原因を1つに絞り、
     根拠とともに1〜3文で述べる。
  4. 根拠を明示した上で、許可された復旧操作を実行する。
  5. 復旧操作の後は、必ず check_health で正常性を検証する。検証せずに終了してはならない。
- 復旧操作が拒否された場合(blocked)、その理由を読み、不足している調査を行ってから再試行する。
- 復旧できない場合は、復旧できなかった事実と理由を正直に報告する。成功したと偽らない。

最終報告は次の3行のみ:
原因: <一文>
実施した操作: <一文>
検証結果: <一文>
"""

KICKOFF_MESSAGE = (
    "シミュレーション環境で障害アラートが発生しました。"
    "対象システムを調査し、原因を特定し、安全な復旧操作を行い、復旧を検証してください。"
)


def build_agent(engine: SimulationEngine, record: RunRecord) -> LlmAgent:
    return LlmAgent(
        name="sre_responder",
        model=GEMINI_MODEL,
        description="クラウド障害の調査・復旧・検証を行う SRE エージェント",
        instruction=INSTRUCTION,
        tools=build_tools(engine),
        before_tool_callback=build_guardrail(record),
        generate_content_config=types.GenerateContentConfig(temperature=0.2),
    )
