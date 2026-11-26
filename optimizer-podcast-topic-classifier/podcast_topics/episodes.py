"""Labeled episode blurbs for Nightlight Audio, a fictional podcast network.

Five topics: science, history, business, true-crime, culture. Several blurbs
straddle two topics on purpose (a heist told as business history, a forensic
lab told as science) because that is where a vague prompt starts guessing.
"""

TOPICS = ["science", "history", "business", "true-crime", "culture"]

# (episode blurb, correct topic)
EPISODES: list[tuple[str, str]] = [
    # --- science ---
    ("How tardigrades survive the vacuum of space, and what their proteins could mean for storing vaccines without a freezer.", "science"),
    ("A glaciologist explains why the ice sheet's underside matters more than its surface for predicting sea level.", "science"),
    ("Inside a neutrino detector buried under a mountain: what it has caught and what it keeps missing.", "science"),
    ("Why do we dream? Sleep researchers argue over memory consolidation versus emotional housekeeping.", "science"),
    ("The forensic entomologist who dates a death by the age of the maggots, and the lab methods behind her estimates.", "science"),
    # --- history ---
    ("The 1854 Broad Street pump: how a mapmaker and a doctor traced cholera to one well in Victorian London.", "history"),
    ("Why the Library of Alexandria really declined: a slow budget crisis, not one dramatic fire.", "history"),
    ("The Hanseatic League's merchant towns and how a trade cartel shaped northern Europe for four centuries.", "history"),
    ("A dockworker's diary from the 1919 Boston molasses flood, read against the court records that followed.", "history"),
    ("How the Dutch tulip bubble of the 1630s became the founding myth of every market crash since.", "history"),
    # --- business ---
    ("A founder explains why she turned down a $40M offer and rebuilt her subscription pricing from scratch.", "business"),
    ("The logistics behind next-day delivery: warehouse slotting, driver routing and the cost of the last mile.", "business"),
    ("What a failed IPO teaches about founder control, lock-up periods and the quiet power of the cap table.", "business"),
    ("Why airlines overbook, how they price the bump, and what it says about customer lifetime value.", "business"),
    ("The coffee chain that expanded to 900 stores in three years, then closed 400 of them in one.", "business"),
    # --- true-crime ---
    ("The 1990 Gardner Museum theft: thirteen works, two guards, and a case that is still open.", "true-crime"),
    ("A small-town pharmacist, a string of poisonings, and the detective who would not accept the first verdict.", "true-crime"),
    ("Twenty years on the run: how a bank robber was finally caught by a retirement-home birthday card.", "true-crime"),
    ("The cold case reopened by a genealogy database, and the family that found out what it had been hiding.", "true-crime"),
    ("Inside a ransomware gang: the negotiation transcripts, the payout and the arrest that followed.", "true-crime"),
    # --- culture ---
    ("Why every streaming drama now has a muted color palette, and who decided prestige should look gray.", "culture"),
    ("The oral history of the fan-edit scene: amateurs re-cutting blockbusters in their bedrooms.", "culture"),
    ("A critic and a novelist argue over whether the sad-girl memoir is a genre or a marketing label.", "culture"),
    ("How a 15-second dance clip became a global festival tradition and then a lawsuit.", "culture"),
    ("The quiet rise of the bookshop cafe, and why people now pay rent to sit near paperbacks.", "culture"),
]
