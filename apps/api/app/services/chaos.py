from dataclasses import dataclass, field
from time import sleep

from fastapi import HTTPException, status

DEFAULT_DEMO_SCENARIO = "default-demo"


@dataclass
class ChaosRule:
    effect: str
    incident_id: str | None
    scenario: str | None
    delay_ms: int = 0


@dataclass
class ChaosRegistry:
    rules: list[ChaosRule] = field(default_factory=list)

    def arm(
        self,
        effect: str,
        incident_id: str | None = None,
        scenario: str | None = None,
        delay_ms: int = 0,
    ) -> ChaosRule:
        target_scenario = scenario if incident_id or scenario else DEFAULT_DEMO_SCENARIO
        rule = ChaosRule(
            effect=effect,
            incident_id=incident_id,
            scenario=target_scenario,
            delay_ms=delay_ms,
        )
        self.rules.append(rule)
        return rule

    def consume(self, incident_id: str | None, scenario: str | None) -> ChaosRule | None:
        for index, rule in enumerate(self.rules):
            if _matches(rule, incident_id, scenario):
                return self.rules.pop(index)
        return None


chaos_registry = ChaosRegistry()


def arm_fail_next(
    incident_id: str | None = None, scenario: str | None = None
) -> dict[str, int | str | None]:
    return _rule_response(chaos_registry.arm("fail_next", incident_id, scenario))


def arm_delay_next(
    delay_ms: int = 750,
    incident_id: str | None = None,
    scenario: str | None = None,
) -> dict[str, int | str | None]:
    rule = chaos_registry.arm("delay_next", incident_id, scenario, max(delay_ms, 0))
    return _rule_response(rule)


def arm_bad_payload_next(
    incident_id: str | None = None, scenario: str | None = None
) -> dict[str, int | str | None]:
    return _rule_response(chaos_registry.arm("return_bad_payload", incident_id, scenario))


def apply_chaos(
    payload: dict | list,
    incident_id: str | None = None,
    scenario: str | None = None,
) -> dict | list:
    rule = chaos_registry.consume(incident_id, scenario)
    if rule is None:
        return payload

    if rule.delay_ms > 0:
        delay_seconds = rule.delay_ms / 1000
        sleep(delay_seconds)

    if rule.effect == "fail_next":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo chaos: product data source failed",
        )

    if rule.effect == "return_bad_payload":
        return {"malformed": True, "items": "not-a-list"}

    return payload


def _matches(rule: ChaosRule, incident_id: str | None, scenario: str | None) -> bool:
    if rule.incident_id is not None and rule.incident_id != incident_id:
        return False
    if rule.scenario is not None and rule.scenario != scenario:
        return False
    return True


def _rule_response(rule: ChaosRule) -> dict[str, int | str | None]:
    return {
        "status": "armed",
        "effect": rule.effect,
        "incident_id": rule.incident_id,
        "scenario": rule.scenario,
        "delay_ms": rule.delay_ms,
    }
