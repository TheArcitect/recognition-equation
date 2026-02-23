"""Core model — the recognition equation R = C - A."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Situation:
    """A scored situation applying R = C - A.

    Contact (C): 0-10 scale. How much genuine interaction is occurring.
        10 = total immersion, full engagement with the subject/person/problem.
        0 = no contact at all.

    Agenda (A): 0-10 scale. How much non-contact the participant brings.
        10 = entirely performing, proving, seeking approval, self-conscious.
        0 = no agenda, pure openness.

    Recognition (R) = C - A. Range: -10 to 10.
        Positive = net recognition (insight, resonance, understanding).
        Zero = agenda exactly cancels contact.
        Negative = agenda exceeds contact (anti-recognition, confusion, blockage).
    """

    name: str = ""
    domain: str = ""
    contact: float = 0.0
    agenda: float = 0.0
    description: str = ""
    contact_factors: list[str] = field(default_factory=list)
    agenda_factors: list[str] = field(default_factory=list)
    ts: str = ""
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.ts:
            self.ts = datetime.now(timezone.utc).isoformat()

    @property
    def recognition(self) -> float:
        """R = C - A."""
        return round(self.contact - self.agenda, 2)

    @property
    def r(self) -> float:
        """Alias for recognition."""
        return self.recognition

    @property
    def efficiency(self) -> Optional[float]:
        """Recognition efficiency: R/C. How much contact converts to recognition."""
        if self.contact == 0:
            return None
        return round(self.recognition / self.contact, 2)

    @property
    def signal_label(self) -> str:
        """Human-readable label for the recognition level."""
        r = self.recognition
        if r >= 7:
            return "breakthrough"
        elif r >= 4:
            return "high recognition"
        elif r >= 1:
            return "moderate recognition"
        elif r >= -1:
            return "near zero"
        elif r >= -4:
            return "blocked"
        else:
            return "anti-recognition"

    def to_json(self) -> str:
        d = {k: v for k, v in asdict(self).items() if v}
        d["recognition"] = self.recognition
        return json.dumps(d)

    @classmethod
    def from_json(cls, line: str) -> Situation:
        data = json.loads(line)
        data.pop("recognition", None)
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)


@dataclass
class Comparison:
    """Side-by-side comparison of two situations."""

    a: Situation
    b: Situation

    @property
    def delta_r(self) -> float:
        return round(self.b.recognition - self.a.recognition, 2)

    @property
    def delta_c(self) -> float:
        return round(self.b.contact - self.a.contact, 2)

    @property
    def delta_a(self) -> float:
        return round(self.b.agenda - self.a.agenda, 2)

    @property
    def primary_driver(self) -> str:
        """What changed most between the two situations?"""
        dc = abs(self.delta_c)
        da = abs(self.delta_a)
        if dc > da:
            return "contact"
        elif da > dc:
            return "agenda"
        else:
            return "both equally"


# Pre-built domain analyses
DOMAIN_EXAMPLES = {
    "education": {
        "high_r": Situation(
            name="Socratic seminar",
            domain="education",
            contact=9, agenda=2,
            description="Small group, question-driven, teacher as facilitator not performer.",
            contact_factors=["direct engagement with material", "student-to-student dialogue", "real questions"],
            agenda_factors=["some grade pressure"],
        ),
        "low_r": Situation(
            name="Lecture hall exam prep",
            domain="education",
            contact=4, agenda=8,
            description="300-person lecture, teaching to the test, performance anxiety.",
            contact_factors=["some exposure to material"],
            agenda_factors=["grades", "performance anxiety", "professor performing expertise", "credential pursuit"],
        ),
    },
    "ai_conversation": {
        "high_r": Situation(
            name="Morning walk dictation",
            domain="ai_conversation",
            contact=9, agenda=1,
            description="Walking, dictating to Claude, exploring without a goal.",
            contact_factors=["embodied movement", "voice input", "no screen", "open exploration"],
            agenda_factors=["minimal — no audience, no deadline"],
        ),
        "low_r": Situation(
            name="Demo for investors",
            domain="ai_conversation",
            contact=6, agenda=9,
            description="Showing Claude to investors, trying to make it perform.",
            contact_factors=["real interaction with AI"],
            agenda_factors=["proving value", "performing for audience", "seeking investment", "curating outputs"],
        ),
    },
    "meetings": {
        "high_r": Situation(
            name="Two people, whiteboard, real problem",
            domain="meetings",
            contact=8, agenda=2,
            description="Small, focused, no status games, genuine problem to solve.",
            contact_factors=["shared problem", "direct dialogue", "physical space"],
            agenda_factors=["slight time pressure"],
        ),
        "low_r": Situation(
            name="All-hands status update",
            domain="meetings",
            contact=3, agenda=8,
            description="50 people, scripted updates, performing for leadership.",
            contact_factors=["some information exchange"],
            agenda_factors=["political positioning", "visibility seeking", "CYA reporting", "forced attendance"],
        ),
    },
    "creativity": {
        "high_r": Situation(
            name="Sketchbook in a cafe",
            domain="creativity",
            contact=8, agenda=1,
            description="Drawing for no one. No deadline, no client, no portfolio.",
            contact_factors=["material engagement", "ambient environment", "embodied practice"],
            agenda_factors=["almost none"],
        ),
        "low_r": Situation(
            name="Client revision round 7",
            domain="creativity",
            contact=5, agenda=9,
            description="Adjusting design to committee feedback. Approval-seeking.",
            contact_factors=["still working with material"],
            agenda_factors=["client approval", "committee consensus", "scope creep", "deadline pressure", "imposter syndrome"],
        ),
    },
    "therapy": {
        "high_r": Situation(
            name="Moment of genuine disclosure",
            domain="therapy",
            contact=9, agenda=2,
            description="Patient stops performing and says what's actually true.",
            contact_factors=["authentic self-contact", "therapist presence", "safety"],
            agenda_factors=["residual self-protection"],
        ),
        "low_r": Situation(
            name="Performing wellness",
            domain="therapy",
            contact=3, agenda=8,
            description="Telling the therapist what sounds healthy. Managing impression.",
            contact_factors=["in the room, technically"],
            agenda_factors=["impression management", "performing progress", "avoiding real material", "seeking approval"],
        ),
    },
}
