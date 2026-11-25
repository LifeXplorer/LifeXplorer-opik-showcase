"""Three fictional course syllabi, rendered to PDF with reportlab.

The courses deliberately disagree on policy (late work, attendance, AI tools),
so an answer is only right if retrieval fetched the right course's section.
Every sentence of a policy starts with the course code for the same reason:
a chunk that is cut out of its page still says whose rule it is.
"""

import pathlib
from dataclasses import dataclass

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas as _canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate

SYLLABI_DIR = pathlib.Path(__file__).parents[1] / "data" / "syllabi"


@dataclass(frozen=True)
class Syllabus:
    code: str
    title: str
    instructor: str
    filename: str
    sections: list[tuple[str, str]]  # (heading, body)


SYLLABI = [
    Syllabus(
        code="BIO 214",
        title="Marine Ecology",
        instructor="Dr. Ingrid Solberg",
        filename="bio-214-marine-ecology.pdf",
        sections=[
            ("Overview", "BIO 214 Marine Ecology is taught by Dr. Ingrid Solberg in the spring term. "
             "BIO 214 covers tidal zonation, kelp forests, plankton dynamics and fisheries collapse, "
             "with four field trips to the Gull Point shoreline."),
            ("Grading", "BIO 214 grades are weighted as follows: field lab reports 40%, midterm exam 20%, "
             "research poster 20%, final exam 20%. A final score of 70% or higher is required to pass BIO 214."),
            ("Late work", "BIO 214 lab reports lose 10% of their mark for every 24 hours they are late. "
             "BIO 214 does not accept a lab report more than 3 days after the deadline: it receives zero."),
            ("Attendance", "BIO 214 field trips are mandatory. Missing a field trip without 48 hours' notice "
             "to Dr. Solberg costs 5% of the final grade. BIO 214 lectures allow up to 3 absences."),
            ("AI tools", "BIO 214 permits AI assistants only to summarise published literature. Any use must "
             "be disclosed in an appendix. BIO 214 does not permit AI tools for data analysis or for writing "
             "the results sections of lab reports."),
            ("Office hours", "BIO 214 office hours are Tuesdays 14:00 to 16:00 in room Tidewater 112."),
        ],
    ),
    Syllabus(
        code="CS 330",
        title="Applied Cryptography",
        instructor="Dr. Tomas Beltran",
        filename="cs-330-applied-cryptography.pdf",
        sections=[
            ("Overview", "CS 330 Applied Cryptography is taught by Dr. Tomas Beltran. CS 330 covers block "
             "ciphers, hash functions, key exchange and TLS, with weekly problem sets and three "
             "implementation projects."),
            ("Grading", "CS 330 grades are weighted as follows: problem sets 30%, implementation projects "
             "30%, midterm exam 15%, final exam 25%. CS 330 has no extra credit."),
            ("Late work", "CS 330 gives every student 4 slip days for the whole term, and at most 2 may be "
             "spent on one assignment. After the slip days are used, CS 330 deducts 20% per day late, and "
             "nothing is accepted more than 2 days past the deadline."),
            ("Attendance", "CS 330 does not grade attendance. Two unannounced in-class quizzes count toward "
             "the problem-set mark and cannot be made up."),
            ("AI tools", "CS 330 allows AI assistants for explaining concepts and for debugging. CS 330 "
             "forbids submitting cryptographic code written by an AI tool. Students must keep a log of "
             "their prompts, and a missing log is treated as an academic-integrity violation."),
            ("Office hours", "CS 330 office hours are Wednesdays 10:00 to 12:00 in room Cipher 301, and "
             "Fridays 15:00 to 16:00 online."),
        ],
    ),
    Syllabus(
        code="HIS 101",
        title="Maritime History",
        instructor="Prof. Amara Nwosu",
        filename="his-101-maritime-history.pdf",
        sections=[
            ("Overview", "HIS 101 Maritime History is taught by Prof. Amara Nwosu. HIS 101 follows trade, "
             "empire and piracy across the Atlantic and Indian oceans from 1450 to 1850."),
            ("Grading", "HIS 101 grades are weighted as follows: weekly reading responses 25%, archive "
             "exercise 20%, midterm essay 20%, final paper 35%."),
            ("Late work", "HIS 101 gives each student one 48-hour extension token, to be requested before "
             "the deadline and without explanation. Without a token, HIS 101 deducts a flat 15% from a late "
             "submission, and nothing is accepted more than 7 days late."),
            ("Attendance", "HIS 101 attendance is required. More than 4 unexcused absences lower the final "
             "grade by one letter step, for example from B+ to B."),
            ("AI tools", "HIS 101 prohibits AI tools for any submitted writing. HIS 101 allows them only for "
             "personal study, such as quizzing yourself on dates and names."),
            ("Office hours", "HIS 101 office hours are Mondays 13:00 to 15:00 in room Anchor 204. There is "
             "no extra-credit work in HIS 101."),
        ],
    ),
]

_styles = getSampleStyleSheet()
_TITLE = ParagraphStyle("T", parent=_styles["Title"], fontName="Helvetica-Bold", fontSize=18)
_META = ParagraphStyle("M", parent=_styles["Normal"], fontName="Helvetica-Oblique", fontSize=10, alignment=1, spaceAfter=14)
_HEAD = ParagraphStyle("H", parent=_styles["Heading2"], fontName="Helvetica-Bold", fontSize=12, spaceBefore=12, spaceAfter=3)
_BODY = ParagraphStyle("B", parent=_styles["Normal"], fontName="Helvetica", fontSize=10.5, leading=14)


def render(syllabus: Syllabus, out_dir: pathlib.Path = SYLLABI_DIR) -> pathlib.Path:
    """Write one syllabus PDF and return its path."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / syllabus.filename
    doc = SimpleDocTemplate(
        str(path), pagesize=A4, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
        topMargin=2.5 * cm, bottomMargin=2.5 * cm,
        title=f"{syllabus.code} {syllabus.title}", author="Northgate University (fictional)",
        canvasmaker=lambda *a, **k: _canvas.Canvas(*a, invariant=1, **k),  # byte-stable output
    )
    story = [
        Paragraph(f"{syllabus.code}: {syllabus.title}", _TITLE),
        Paragraph(f"{syllabus.instructor} · Northgate University", _META),
    ]
    for heading, body in syllabus.sections:
        story += [Paragraph(heading, _HEAD), Paragraph(body, _BODY)]
    doc.build(story)
    return path


def ensure_corpus(out_dir: pathlib.Path = SYLLABI_DIR) -> list[pathlib.Path]:
    """Return the syllabus PDFs, generating any that are missing."""
    return [
        (out_dir / s.filename) if (out_dir / s.filename).exists() else render(s, out_dir)
        for s in SYLLABI
    ]
