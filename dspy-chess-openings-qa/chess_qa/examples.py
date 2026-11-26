"""Worked tickets for compiling, and held-out tickets for testing."""

import dspy

from .handbook import HANDBOOK

# (question, house-format answer, card id, key fact). The house format is the
# bare answer, then " | card: <ID>". It appears only here, never in an instruction.
TRAIN_ROWS = [
    ("Which moves define the Italian Game?",
     "1.e4 e5 2.Nf3 Nc6 3.Bc4 | card: ITA-1", "ITA-1", "3.Bc4"),
    ("What does White play on move 2 of the Open Sicilian?",
     "2.Nf3 | card: SIC-2", "SIC-2", "2.Nf3"),
    ("How does White continue after 2.c4 in the Queen's Gambit?",
     "Play 1.d4 d5 2.c4 | card: QGD-1", "QGD-1", "2.c4"),
    ("Which piece is the French Defence's problem piece?",
     "The light-squared bishop on c8 | card: FRE-1", "FRE-1", "bishop on c8"),
    ("Which pawn moves does the London System use?",
     "e3 and c3 | card: LON-1", "LON-1", "e3"),
    ("Where does Black develop the bishop in the Caro-Kann?",
     "f5 | card: CAR-1", "CAR-1", "f5"),
    ("What are the first two moves of the Sicilian Defence?",
     "1.e4 c5 | card: SIC-1", "SIC-1", "1.e4 c5"),
    ("What is the quiet Italian plan called by coaches?",
     "The slow cooker line | card: ITA-2", "ITA-2", "slow cooker"),
]

# (question, card id, key fact, plain-language assertion for the Opik suite).
# None of these appear in TRAIN_ROWS, so the compiled demos have to transfer.
TEST_ROWS = [
    ("Who does not play the Sicilian in club ladder games?",
     "SIC-1", "under 12", "The answer says juniors under 12 do not play it"),
    ("By which move should the quiet Italian castle?",
     "ITA-2", "move 6", "The answer says castling comes no later than move 6"),
    ("How does White regain the pawn after 2...dxc4 in the Queen's Gambit?",
     "QGD-1", "Bxc4", "The answer says White plays e3 and Bxc4"),
    ("How does White recapture after 3...cxd4 in the Open Sicilian?",
     "SIC-2", "4.Nxd4", "The answer says the knight recaptures with 4.Nxd4"),
    ("Which pawn locks in the French Defence bishop?",
     "FRE-1", "e6", "The answer says the e6 pawn locks the bishop in"),
    ("Which London System developing move comes first, e3 or Bf4?",
     "LON-1", "Bf4", "The answer says the bishop goes to f4 before e3"),
    ("Why does the Caro-Kann bishop never get locked in?",
     "CAR-1", "...Bf5", "The answer says Black plays ...Bf5 before ...e6"),
    ("Why does Rookfield teach the Italian Game first?",
     "ITA-1", "obvious square", "The answer says every piece has an obvious square"),
]


def _example(question, answer, card, fact):
    return dspy.Example(
        context=HANDBOOK, question=question, answer=answer, card=card, key_fact=fact
    ).with_inputs("context", "question")


trainset = [_example(q, a, c, f) for q, a, c, f in TRAIN_ROWS]
# Test examples carry no reference answer: only the card and fact the metric checks.
testset = [_example(q, "", c, f) for q, c, f, _ in TEST_ROWS]
