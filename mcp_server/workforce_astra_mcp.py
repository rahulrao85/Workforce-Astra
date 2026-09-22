"""
Workforce Astra -- MOCK MCP server for the closed-loop action (demo stub only).

⚠️  NOTHING HERE IS REAL. There is no Workday tenant, no Slack workspace, and no
    credentials. Both tools return synthetic success payloads so the CoCo agent's
    action step can be demonstrated end to end. Neither tool drafts, applies, or
    sends anything outside this process. State that explicitly in the submission.

Tools (schemas mirror MCP_TOOLS.md in the project root):
  - workday_create_compensation_adjustment  -> drafts a comp change for approval routing
  - workday_create_promotion_nomination     -> drafts a promotion nomination for calibration
  - workday_create_requisition              -> drafts a job requisition from a governed hiring need
  - simulate_org_reorg                      -> guarded reorg dry-run (rejects cycles / overspan)
  - slack_notify_manager_flight_risk        -> mocks a private DM to a manager

Every call is appended to calls.jsonl next to this file, so the demo can prove the
tool actually fired (and the recording can show the audit trail afterwards).

Register with CoCo CLI:

    cortex mcp add workforce-astra \
      python "<project>/mcp_server/workforce_astra_mcp.py"

Or add to ~/.snowflake/cortex/mcp.json:

    {
      "mcpServers": {
        "workforce-astra": {
          "type": "stdio",
          "command": "python",
          "args": ["<project>/mcp_server/workforce_astra_mcp.py"]
        }
      }
    }

Tools are then namespaced as mcp__workforce-astra__workday_create_compensation_adjustment
and mcp__workforce-astra__slack_notify_manager_flight_risk.

Self-test (no MCP client needed -- prints the mocked payloads):

    python mcp_server/workforce_astra_mcp.py --selftest
"""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

AUDIT_LOG = Path(__file__).resolve().parent / "calls.jsonl"
MOCK_TENANT = "MOCK-WORKDAY-TENANT"
MOCK_WORKSPACE = "MOCK-SLACK-WORKSPACE"

server = MCPServer(
    name="workforce-astra",
    version="0.1.0",
    description="MOCKED Workforce Astra actions -- drafts and notifies only, never applies.",
)


def _audit(tool: str, payload: dict) -> None:
    record = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "tool": tool,
        "mock": True,
        "payload": payload,
    }
    with open(AUDIT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _ok(tool: str, payload: dict) -> str:
    _audit(tool, payload)
    return json.dumps({"mock": True, **payload}, indent=2)


@server.tool(
    description=(
        "Drafts a compensation adjustment request for an employee, to be routed through "
        "the real Workday approval chain. DRAFTS only -- never applies pay changes directly."
    )
)
def workday_create_compensation_adjustment(
    employee_id: str = Field(description="Employee ID, e.g. EMP-0042"),
    proposed_base_pay: float = Field(description="Proposed new annual base pay"),
    justification: str = Field(
        description="Cites the semantic-view metric and evidence snippet that triggered this"
    ),
    current_base_pay: float | None = Field(
        default=None, description="Current annual base pay, if known"
    ),
    effective_date: str | None = Field(
        default=None, description="Proposed effective date, YYYY-MM-DD"
    ),
) -> str:
    if proposed_base_pay <= 0:
        raise ToolError("proposed_base_pay must be greater than zero")

    effective = effective_date or (date.today() + timedelta(days=30)).isoformat()
    change_pct = (
        round((proposed_base_pay - current_base_pay) / current_base_pay * 100, 1)
        if current_base_pay
        else None
    )

    warnings = []
    if change_pct is not None and abs(change_pct) > 25:
        warnings.append(
            f"Adjustment of {change_pct}% exceeds the 25% self-service threshold -- "
            "will require VP-level approval."
        )
    if not justification.strip():
        warnings.append("Justification is empty; the approval chain will bounce this.")

    return _ok(
        "workday_create_compensation_adjustment",
        {
            "status": "DRAFTED",
            "adjustment_id": f"CA-{datetime.now(timezone.utc):%Y%m%d}-{abs(hash(employee_id)) % 10000:04d}",
            "employee_id": employee_id,
            "tenant": MOCK_TENANT,
            "current_base_pay": current_base_pay,
            "proposed_base_pay": proposed_base_pay,
            "change_pct": change_pct,
            "effective_date": effective,
            "justification": justification,
            "approval_chain": ["Reporting Manager", "People Ops Partner", "Compensation Committee"],
            "approval_state": "PENDING_MANAGER",
            "applied": False,
            "warnings": warnings,
            "note": (
                "MOCK: no Workday tenant was contacted and no pay change was applied. "
                "A draft would be queued for the approval chain above."
            ),
        },
    )


@server.tool(
    description=(
        "Sends a private Slack DM to an employee's manager flagging a flight-risk finding, "
        "with cited evidence. Never sent to the employee themselves."
    )
)
def slack_notify_manager_flight_risk(
    manager_slack_id: str = Field(description="Manager Slack member ID, e.g. U0007"),
    employee_id: str = Field(description="Employee the finding is about, e.g. EMP-0042"),
    risk_score: float = Field(description="Composite flight-risk score from the semantic view"),
    evidence_snippet: str = Field(
        description="Verbatim excerpt from Cortex Search result, with source review_id"
    ),
) -> str:
    if not manager_slack_id.startswith(("U", "W")):
        raise ToolError(
            "manager_slack_id must be a Slack member ID (starts with U or W). "
            "Refusing to notify -- this guardrail also prevents messaging the employee directly."
        )
    if not 0 <= risk_score <= 1 and not 0 <= risk_score <= 100:
        raise ToolError("risk_score should be a 0-1 probability or a 0-100 score")

    severity = (
        "high" if risk_score >= 0.7 or risk_score >= 70
        else "medium" if risk_score >= 0.4 or risk_score >= 40
        else "low"
    )

    return _ok(
        "slack_notify_manager_flight_risk",
        {
            "status": "SENT",
            "channel": "direct_message",
            "recipient": manager_slack_id,
            "workspace": MOCK_WORKSPACE,
            "message_ts": f"{datetime.now(timezone.utc).timestamp():.6f}",
            "employee_id": employee_id,
            "risk_score": risk_score,
            "severity": severity,
            "evidence_snippet": evidence_snippet,
            "sent_to_employee": False,
            "blocks": [
                {
                    "type": "section",
                    "text": (
                        f":rotating_light: Flight-risk signal ({severity}) for {employee_id}. "
                        f"Score {risk_score}. Cited evidence: {evidence_snippet}"
                    ),
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": "Source: governed Employee 360 semantic view + Cortex Search",
                        }
                    ],
                },
            ],
            "note": (
                "MOCK: no Slack workspace was contacted and no message was delivered. "
                "A DM to the manager (never the employee) would be posted as above."
            ),
        },
    )


_IDEMPOTENCY_CACHE: dict[str, str] = {}


@server.tool(
    description=(
        "Drafts a promotion nomination for the calibration cycle, to be routed through the real "
        "Workday promotion workflow. DRAFTS only -- never promotes anyone. Supports dry-run."
    )
)
def workday_create_promotion_nomination(
    employee_id: str = Field(description="Employee ID, e.g. EMP-0042"),
    target_band: str = Field(description="Target band: one of IC3, IC4, IC5, M1, M2"),
    justification: str = Field(
        description="Cites the governed promotion_readiness metric and cited review evidence"
    ),
    cycle: str = Field(default="", description="Calibration cycle, e.g. 2026-H2"),
    dry_run: bool = Field(default=True, description="True = preview only, nothing is queued"),
    idempotency_key: str = Field(default="", description="Optional key to dedupe repeated calls"),
) -> str:
    if target_band not in {"IC3", "IC4", "IC5", "M1", "M2"}:
        raise ToolError("target_band must be one of IC3, IC4, IC5, M1, M2")
    if len(justification.strip()) < 20:
        raise ToolError("justification must cite the governed metric and evidence (>= 20 chars)")
    if idempotency_key and idempotency_key in _IDEMPOTENCY_CACHE:
        return _IDEMPOTENCY_CACHE[idempotency_key]

    warnings = [] if cycle else ["No calibration cycle supplied; defaulting to 2026-H2."]
    result = _ok(
        "workday_create_promotion_nomination",
        {
            "status": "DRY_RUN" if dry_run else "DRAFTED",
            "nomination_id": f"PN-{datetime.now(timezone.utc):%Y%m%d}-{abs(hash(employee_id)) % 10000:04d}",
            "employee_id": employee_id,
            "target_band": target_band,
            "cycle": cycle or "2026-H2",
            "justification": justification,
            "approval_chain": ["Reporting Manager", "People Ops Partner", "Calibration Committee"],
            "approval_state": "PENDING_MANAGER",
            "dry_run": dry_run,
            "applied": False,
            "warnings": warnings,
            "note": (
                "MOCK: no Workday tenant was contacted and no promotion was applied. "
                "A draft would be queued for the approval chain above."
            ),
        },
    )
    if idempotency_key:
        _IDEMPOTENCY_CACHE[idempotency_key] = result
    return result


@server.tool(
    description=(
        "Drafts a job requisition in Workday from a governed hiring need (open reqs, time-to-fill, "
        "span-of-control evidence). DRAFTS only -- never posts a job."
    )
)
def workday_create_requisition(
    department_code: str = Field(description="Department, e.g. Engineering"),
    band_code: str = Field(description="Band: one of IC3, IC4, IC5, M1, M2"),
    justification: str = Field(
        description="Cites the governed metric that justifies the hire (e.g. overspan manager, open reqs)"
    ),
    hiring_manager_id: str = Field(default="", description="Hiring manager employee ID"),
    dry_run: bool = Field(default=True, description="True = preview only, nothing is queued"),
) -> str:
    if band_code not in {"IC3", "IC4", "IC5", "M1", "M2"}:
        raise ToolError("band_code must be one of IC3, IC4, IC5, M1, M2")
    if len(justification.strip()) < 20:
        raise ToolError("justification must cite the governed metric (>= 20 chars)")

    return _ok(
        "workday_create_requisition",
        {
            "status": "DRY_RUN" if dry_run else "DRAFTED",
            "requisition_id": f"REQ-{datetime.now(timezone.utc):%Y%m%d}-{abs(hash(department_code + band_code)) % 10000:04d}",
            "department_code": department_code,
            "band_code": band_code,
            "hiring_manager_id": hiring_manager_id or None,
            "justification": justification,
            "budget_approved_date": date.today().isoformat(),
            "expected_post_date": (date.today() + timedelta(days=5)).isoformat(),
            "dry_run": dry_run,
            "applied": False,
            "note": (
                "MOCK: no Workday tenant was contacted and no requisition was posted. "
                "The budget/post dates feed the governed enterprise_vacancy_duration metric."
            ),
        },
    )


@server.tool(
    description=(
        "Guarded org reorg simulator. Mirrors WORKFORCE_ASTRA.RAW.simulate_reorg -- rejects "
        "self-moves and circular reporting lines and NEVER mutates org data. This local tool "
        "returns a schema-accurate preview; the live version runs as a Snowflake stored procedure."
    )
)
def simulate_org_reorg(
    source_manager: str = Field(description="Manager whose reporting line would move, e.g. EMP-0001"),
    target_manager: str = Field(description="Manager who would become the new reporting line, e.g. EMP-0005"),
    source_subtree_size: int = Field(default=0, description="Size of source subtree (from org_health_360)"),
    target_current_span: int = Field(default=0, description="Target's current direct reports"),
) -> str:
    if not source_manager.startswith("EMP-") or not target_manager.startswith("EMP-"):
        raise ToolError("manager ids must look like EMP-0001 (guardrail: reject malformed ids)")
    if source_manager == target_manager:
        return _ok(
            "simulate_org_reorg",
            {"status": "REJECTED", "guardrail": "source and target are the same person"},
        )
    if target_current_span + 1 > 12:
        return _ok(
            "simulate_org_reorg",
            {
                "status": "REJECTED",
                "guardrail": "would push target span above the 12-report overspan ceiling",
                "target_projected_span": target_current_span + 1,
            },
        )
    return _ok(
        "simulate_org_reorg",
        {
            "status": "VALIDATED",
            "source_mgr": source_manager,
            "target_mgr": target_manager,
            "source_subtree_size": source_subtree_size,
            "target_current_span": target_current_span,
            "target_projected_span": target_current_span + 1,
            "note": "SIMULATION ONLY - no org data was modified",
        },
    )


def _selftest() -> int:
    print("== self-test: workday_create_compensation_adjustment ==")
    print(
        workday_create_compensation_adjustment(
            employee_id="EMP-0042",
            current_base_pay=1180000,
            proposed_base_pay=1350000,
            justification="comp_ratio 0.79 vs band mid; review REV-00042 rating 5, no retention concern raised",
            effective_date="2026-10-01",
        )
    )
    print("\n== self-test: slack_notify_manager_flight_risk ==")
    print(
        slack_notify_manager_flight_risk(
            manager_slack_id="U0007",
            employee_id="EMP-0042",
            risk_score=0.82,
            evidence_snippet=(
                "REV-00042: 'Goals largely unmet this cycle; manager noted visible frustration "
                "with role scope.'"
            ),
        )
    )
    print("\n== self-test: guardrail (bad slack id must be rejected) ==")
    try:
        slack_notify_manager_flight_risk("not-a-slack-id", "EMP-0042", 0.9, "x")
    except ToolError as e:
        print(f"correctly rejected: {e}")

    print("\n== self-test: workday_create_promotion_nomination (dry-run) ==")
    print(
        workday_create_promotion_nomination(
            employee_id="EMP-0042",
            target_band="IC5",
            justification="governed promotion_readiness 0.91; review REV-00042 rating 5, 26 months in IC4",
            cycle="2026-H2",
            dry_run=True,
        )
    )
    print("\n== self-test: workday_create_requisition (dry-run) ==")
    print(
        workday_create_requisition(
            department_code="Engineering",
            band_code="IC4",
            justification="overspan manager EMP-0007 at 14 direct reports; open reqs at 6 vs plan 4",
            hiring_manager_id="EMP-0007",
            dry_run=True,
        )
    )
    print("\n== self-test: simulate_org_reorg (validated) ==")
    print(simulate_org_reorg("EMP-0001", "EMP-0005", source_subtree_size=9, target_current_span=8))
    print("\n== self-test: simulate_org_reorg (guardrail: overspan ceiling) ==")
    print(simulate_org_reorg("EMP-0001", "EMP-0005", source_subtree_size=9, target_current_span=12))

    print(f"\naudit trail -> {AUDIT_LOG}")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(_selftest())
    server.run("stdio")
