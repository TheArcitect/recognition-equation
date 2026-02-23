"""Tests for the recognition equation model."""

from rec_eq.model import Situation, Comparison, DOMAIN_EXAMPLES


def test_basic_calculation():
    s = Situation(contact=8, agenda=2)
    assert s.recognition == 6.0
    assert s.r == 6.0


def test_negative_recognition():
    s = Situation(contact=3, agenda=9)
    assert s.recognition == -6.0


def test_zero_recognition():
    s = Situation(contact=5, agenda=5)
    assert s.recognition == 0.0


def test_efficiency():
    s = Situation(contact=10, agenda=2)
    assert s.efficiency == 0.8

    s2 = Situation(contact=0, agenda=5)
    assert s2.efficiency is None


def test_signal_labels():
    assert Situation(contact=10, agenda=1).signal_label == "breakthrough"
    assert Situation(contact=8, agenda=3).signal_label == "high recognition"
    assert Situation(contact=6, agenda=4).signal_label == "moderate recognition"
    assert Situation(contact=5, agenda=5).signal_label == "near zero"
    assert Situation(contact=3, agenda=6).signal_label == "blocked"
    assert Situation(contact=1, agenda=9).signal_label == "anti-recognition"


def test_roundtrip_json():
    s = Situation(
        name="test", domain="testing",
        contact=7, agenda=3,
        description="A test situation",
        contact_factors=["factor1"],
        agenda_factors=["factor2"],
    )
    json_str = s.to_json()
    s2 = Situation.from_json(json_str)
    assert s2.name == "test"
    assert s2.contact == 7
    assert s2.agenda == 3
    assert s2.recognition == 4.0


def test_comparison():
    a = Situation(name="low", contact=3, agenda=8)
    b = Situation(name="high", contact=9, agenda=2)
    comp = Comparison(a=a, b=b)

    assert comp.delta_r == 12.0  # from -5 to 7
    assert comp.delta_c == 6.0
    assert comp.delta_a == -6.0
    assert comp.primary_driver == "both equally"


def test_comparison_contact_driven():
    a = Situation(contact=3, agenda=5)
    b = Situation(contact=9, agenda=5)
    comp = Comparison(a=a, b=b)
    assert comp.primary_driver == "contact"


def test_comparison_agenda_driven():
    a = Situation(contact=7, agenda=8)
    b = Situation(contact=7, agenda=2)
    comp = Comparison(a=a, b=b)
    assert comp.primary_driver == "agenda"


def test_domain_examples_exist():
    assert "education" in DOMAIN_EXAMPLES
    assert "ai_conversation" in DOMAIN_EXAMPLES
    assert "meetings" in DOMAIN_EXAMPLES
    assert "creativity" in DOMAIN_EXAMPLES
    assert "therapy" in DOMAIN_EXAMPLES


def test_domain_examples_valid():
    for domain, examples in DOMAIN_EXAMPLES.items():
        high = examples["high_r"]
        low = examples["low_r"]
        assert high.recognition > low.recognition, f"{domain}: high_r should have higher R than low_r"
        assert high.contact >= 0 and high.contact <= 10
        assert low.agenda >= 0 and low.agenda <= 10
