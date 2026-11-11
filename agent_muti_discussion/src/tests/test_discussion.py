"""Regression tests for the current SessionManager API (no external model calls)."""
import pytest


@pytest.fixture
def session(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "s01-offline-test-key")
    from agent_muti_discussion.src.core.session_manager import SessionManager
    manager = SessionManager(max_rounds=3)
    monkeypatch.setattr(manager.analyzer, "process", lambda q: {"analyzed_requirement": q})
    for name, expert in manager.experts.items():
        monkeypatch.setattr(expert, "process", lambda q, context=None, name=name: {
            "expert_name": name, "expert_logic": "test summary", "opinion": "same supported observation"})
    monkeypatch.setattr(manager.moderator, "process", lambda *a, **k: {
        "moderator_decision": "end", "discussion_complete": True})
    monkeypatch.setattr(manager.moderator, "generate_response", lambda prompt: "final summary")
    yield manager
    manager.analyzer.llm.close()
    manager.moderator.llm.close()
    for expert in manager.experts.values():
        expert.llm.close()


def test_current_session_produces_all_experts_and_summary(session):
    result = session.process_user_input("sample requirement")
    assert result["final_summary"]["summary"] == "final summary"
    assert result["final_summary"]["total_opinions"] == 3
    assert len(result["discussion_history"]) == 1


def test_session_is_reset_between_queries(session):
    session.process_user_input("first")
    second = session.process_user_input("second")
    assert second["original_question"] == "second"
    assert len(second["discussion_history"]) == 1
    assert second["discussion_rounds"] == 1


def test_consensus_current_contract():
    from agent_muti_discussion.src.core.consensus_checker import ConsensusChecker
    result = ConsensusChecker().check_consensus([
        {"expert_name": "a", "opinion": "same"}, {"expert_name": "b", "opinion": "same"}])
    assert result["consensus_achieved"] is True
    assert result["differences_found"] == 0
