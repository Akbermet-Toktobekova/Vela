import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from pydantic import ValidationError

from vela import ai
from vela.specialist_agents import (AnalysisBundle, Proposal, Reference, ROLES,
                                    analyze_bundle, analyze_specialist, validate_proposal)


def fixture():
    return AnalysisBundle(run_id="run-a", financial_revision=7, preference_version=2,
                          policy_version="provisional-v1", focus="goal", income_type="irregular",
                          preferences=("Prefer smaller steps",), restrictions=("No investments",),
                          references=tuple(Reference(id=f"{role}-{kind}", role=role, kind=kind,
                              description="Verified calculator output / explicit unknown")
                              for role in ROLES for kind in ("evidence", "candidate", "missing_input")))


def proposal(bundle, role):
    return Proposal(run_id=bundle.run_id, financial_revision=bundle.financial_revision,
                    preference_version=bundle.preference_version, policy_version=bundle.policy_version,
                    role=role, evidence_ids=(f"{role}-evidence",),
                    candidate_ids=(f"{role}-candidate",), missing_input_ids=(f"{role}-missing_input",))


class SpecialistTests(unittest.IsolatedAsyncioTestCase):
    async def test_three_roles_same_profile_versions_and_scoped_evidence(self):
        bundle = fixture()
        before = bundle.model_dump_json()
        calls = []

        async def generate(quotas, route, contents, config, **kwargs):
            payload = json.loads(contents)
            role = payload["references"][0]["role"]
            calls.append((role, payload, config))
            return SimpleNamespace(text=proposal(bundle, role).model_dump_json()), "mock-flash"

        with patch.object(ai, "generate", side_effect=generate):
            results = await analyze_bundle(bundle, None)
        self.assertEqual([r.role for r in results], list(ROLES))
        self.assertTrue(all(r.status == "succeeded" for r in results))
        self.assertEqual(len(calls), 3)
        for role, payload, config in calls:
            self.assertEqual(payload["preferences"], ["Prefer smaller steps"])
            self.assertEqual(payload["restrictions"], ["No investments"])
            self.assertEqual(payload["financial_revision"], 7)
            self.assertTrue(all(ref["role"] == role for ref in payload["references"]))
            self.assertIn("untrusted data", config["system_instruction"])
        self.assertEqual(before, bundle.model_dump_json())

    async def test_rejects_invented_foreign_wrong_kind_duplicate_and_unbacked_candidates(self):
        bundle = fixture()
        base = proposal(bundle, "debt")
        changes = [dict(candidate_ids=("invented",)), dict(candidate_ids=("cash_flow-candidate",)),
                   dict(candidate_ids=("debt-evidence",)),
                   dict(evidence_ids=("debt-evidence", "debt-evidence")), dict(evidence_ids=())]
        for change in changes:
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    validate_proposal(bundle, "debt", base.model_copy(update=change))

    async def test_every_version_and_role_is_checked(self):
        bundle = fixture()
        for change in (dict(run_id="foreign"), dict(financial_revision=8),
                       dict(preference_version=3), dict(policy_version="different"),
                       dict(role="cash_flow")):
            with self.assertRaises(ValueError):
                validate_proposal(bundle, "debt", proposal(bundle, "debt").model_copy(update=change))

    async def test_invalid_json_and_model_money_fail_closed(self):
        bundle = fixture()
        for text in ("not json", json.dumps({**proposal(bundle, "debt").model_dump(), "amount": 999}),
                     proposal(bundle, "debt").model_copy(update={"financial_revision": 99}).model_dump_json()):
            with patch.object(ai, "generate", AsyncMock(return_value=(SimpleNamespace(text=text), "mock"))):
                result = await analyze_specialist(bundle, "debt", None)
            self.assertEqual(result.status, "failed")
            self.assertIsNone(result.proposal)

    async def test_unavailable_is_not_no_debt(self):
        with patch.object(ai, "generate", AsyncMock(side_effect=ai.AIUnavailable("off"))):
            results = await analyze_bundle(fixture(), None)
        self.assertTrue(all(r.status == "unavailable" and r.proposal is None for r in results))

    async def test_timeout_cancels_provider(self):
        cancelled = asyncio.Event()

        async def slow(*args, **kwargs):
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        with patch.object(ai, "generate", side_effect=slow):
            result = await analyze_specialist(fixture(), "debt", None, timeout_seconds=1)
        self.assertEqual(result.status, "timed_out")
        self.assertTrue(cancelled.is_set())

    async def test_bundle_is_immutable_and_bounded(self):
        bundle = fixture()
        with self.assertRaises(ValidationError):
            bundle.financial_revision = 9
        with self.assertRaises(ValidationError):
            AnalysisBundle.model_validate({**bundle.model_dump(), "preferences": ["x" * 201]})
        with self.assertRaises(ValidationError):
            AnalysisBundle.model_validate({**bundle.model_dump(), "references": [bundle.references[0]] * 2})

    async def test_off_switch_uses_existing_gateway_without_sdk_call(self):
        with patch.object(ai, "enabled", return_value=False):
            result = await analyze_specialist(fixture(), "debt", None)
        self.assertEqual(result.status, "unavailable")
