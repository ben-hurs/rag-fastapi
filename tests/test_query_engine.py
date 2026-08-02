import pytest
from src.query_engine import answer_question

@pytest.mark.llm
def test_reembolso():
    r = answer_question("quantos dias tenho para pedir reembolso?")
    assert "30" in r.answer
    assert len(r.sources) > 0

@pytest.mark.llm
def test_sla():
    r = answer_question("qual o SLA de resposta do suporte?")
    assert "24" in r.answer