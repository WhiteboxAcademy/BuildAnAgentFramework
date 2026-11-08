"""Provided: 42 test questions, fixed before any measuring, and how to mark them.

Each row is (name, kind, question, answers, files). A run passes if the answer contains any of
the answers. An empty list of answers means the documents don't say, so the right reply is
"I don't know". files lists every file needed for the answer.

Two checks were corrected after they marked right answers wrong: hair accepts "tie" as well as
"tied", and loyalty accepts "ten" as well as "tenth" and "10".
"""
from whitebox import Case, Check

HANDBOOK = [
    # direct: the wording is close to the document
    ("drink-recipe", "direct", "How many grams of coffee and espresso does the house blend recipe use?", ["18", "36"], ["espresso-recipe.md"]),
    ("float", "direct", "How much is the till float?", ["150"], ["cash-handling.md"]),
    ("payday", "direct", "When is payday?", ["last Friday"], ["wages.md"]),
    ("milk-charge", "direct", "How much extra do oat, soya and coconut milk cost?", ["45p"], ["milk-and-alternatives.md"]),
    ("fridge", "direct", "What temperature must fridges stay at?", ["5°C", "5 °C", "5 degrees"], ["food-safety.md"]),
    ("grounds", "direct", "When are coffee grounds collected?", ["Tuesday"], ["waste-and-recycling.md"]),
    ("hot-food", "direct", "What temperature must hot food reach in the centre?", ["75"], ["food-safety.md"]),
    ("loyalty", "direct", "How many hot drinks until a customer gets a free one on the loyalty card?", ["tenth", "10", "ten"], ["loyalty-card.md"]),
    # gap: the question avoids the document's words
    ("holiday", "gap", "How many vacation days do I get as a full-timer?", ["28"], ["annual-leave.md"]),
    ("quit", "gap", "I'm a barista and I want to quit. How much warning do I have to give?", ["2 weeks", "two weeks"], ["resignation.md"]),
    ("feel-ill", "gap", "I woke up feeling awful and can't make it in. How do I let my boss know?", ["phone", "call"], ["sickness-absence.md"]),
    ("funeral", "gap", "My dad just passed away. How much paid time can I have?", ["5"], ["bereavement-leave.md"]),
    ("mice", "gap", "I found evidence of mice in the storeroom. Who handles that?", ["Halden"], ["food-safety.md"]),
    ("scald", "gap", "I scalded my hand on the steam wand. How long should I hold it under the tap?", ["20"], ["first-aid.md"]),
    ("shoes", "gap", "Can I get money back for buying work footwear?", ["40"], ["uniform.md"]),
    ("hair", "gap", "Do I need to do anything about my ponytail at work?", ["tied", "tie"], ["uniform.md"]),
    # code: exact identifiers
    ("e44", "code", "What does E44 mean?", ["dose sensor"], ["grinder-errors.md"]),
    ("e31", "code", "The grinder shows E31. What do I do?", ["20"], ["grinder-errors.md"]),
    ("r5", "code", "What is refund reason code R5 for?", ["price"], ["refunds.md"]),
    ("ir9", "code", "What is form IR-9 for?", ["data breach"], ["forms.md"]),
    ("hr15", "code", "What is HR-15?", ["flexible"], ["forms.md"]),
    ("fn6", "code", "What is FN-6 used for?", ["bank"], ["forms.md"]),
    # hop: needs two documents
    ("harbour-arrive", "hop", "I'm opening the Harbour branch on a Monday. What time do I need to arrive?", ["06:00", "6:00", "6 am", "6am"], ["branch-harbour.md", "shifts.md"]),
    ("senior-beans", "hop", "I'm a senior barista. What discount do I get on retail beans?", ["25%"], ["pay-bands.md", "staff-discount.md"]),
    ("riverside-repair", "hop", "The espresso machine at Riverside has broken. What number do I call?", ["0300 555 0177"], ["branch-riverside.md", "equipment-repairs.md"]),
    ("shift-lead-pay", "hop", "What is the hourly rate for a shift lead?", ["14.75"], ["pay-bands.md", "wages.md"]),
    ("lead-notice", "hop", "I'm a shift lead. How much notice must I give when I resign?", ["4 weeks", "four weeks"], ["pay-bands.md", "resignation.md"]),
    ("old-mill-repair", "hop", "Who do I call to repair the grinder at Old Mill, and on what number?", ["0300 555 0142"], ["branch-old-mill.md", "equipment-repairs.md"]),
    # none: the handbook doesn't say
    ("pension", "none", "What percentage does Quillon match on pension contributions?", [], []),
    ("dental", "none", "Does Quillon offer dental insurance?", [], []),
    ("wifi", "none", "What is the customer wifi password at Harbour?", [], []),
    ("dogs", "none", "Are dogs allowed inside the Riverside branch?", [], []),
]

RECORDS = [
    ("flood", "records", "How much stock was lost when the Harbour cellar flooded?", ["640"], ["log-harbour-2025-02.md"]),
    ("cupping-guest", "records", "Who was the guest at the Riverside cupping club in June 2025?", ["Anika Voss"], ["log-riverside-2025-06.md"]),
    ("film-crew", "records", "How much did the film crew pay to use Old Mill?", ["350"], ["log-old-mill-2025-08.md"]),
    ("card-reader", "records", "How long was the Station card reader down just before Christmas 2025?", ["11:15", "3 hours", "three hours"], ["log-station-2025-12.md"]),
    ("ferry-order", "records", "How many flat whites did the ferry company order for the Saturday crew breakfast?", ["40"], ["log-harbour-2025-09.md"]),
    ("fennel-min", "records", "What is the minimum order with Fennel Bakehouse?", ["60"], ["suppliers.md"]),
    ("tidewater-fee", "records", "How much is a Tidewater call-out?", ["85"], ["suppliers.md"]),
    ("lantern-price", "records", "How much is a 250g bag of Lantern?", ["8.50"], ["products-beans.md"]),
    ("records-none", "none", "What did the health inspector score the Station branch in 2025?", [], []),
    ("records-none2", "none", "How much did the Riverside roof repair cost in 2025?", [], []),
]


# A stricter check for the hop questions, added in this chapter after reading the passes.
# name: (the answer must say one of these, and it must say none of these)
STRICT = {
    "harbour-arrive": (["06:00", " 6:00", "6 am", "6am"], []),
    "senior-beans": (["25%"], ["15%", "30%"]),
    "riverside-repair": (["0300 555 0177"], ["0300 555 0142"]),
    "shift-lead-pay": (["14.75"], ["12.60", "16.90"]),
    "lead-notice": (["4 weeks", "four weeks"], ["2 weeks", "8 weeks"]),
    "old-mill-repair": (["0300 555 0142"], ["0300 555 0177"]),
}


def says(answer, texts):
    return any(text.lower() in answer.lower() for text in texts)


def strict_pass(answer, name):
    must, must_not = STRICT[name]
    return says(answer, must) and not says(answer, must_not)


def any_of(answers):
    return Check(f"any of {answers}", lambda result: any(text.lower() in result.answer.lower() for text in answers))


def says_unknown():
    return Check("says I don't know", lambda result: "don't know" in result.answer.lower().replace("’", "'"))


def to_case(row):
    name, kind, question, answers, files = row
    return Case(f"{kind}:{name}", question, [any_of(answers) if answers else says_unknown()])


def to_cases(rows):
    return [to_case(row) for row in rows]


def file_cases(rows):
    """The (question, files) pairs that hit_rate takes, leaving out questions with no file."""
    return [(row[2], row[4]) for row in rows if row[4]]


def by_kind(report):
    """Add up a report's passes for each kind of question."""
    kinds = {}
    for row in report.rows:
        kind = row.name.split(":")[0]
        passed, runs = kinds.get(kind, (0, 0))
        kinds[kind] = (passed + row.passed, runs + row.runs)
    return kinds


def summary(report):
    passed, runs = report.score()
    parts = [f"{kind} {done}/{total}" for kind, (done, total) in by_kind(report).items()]
    return f"{report.label:<21} {passed:>3}/{runs}  " + "  ".join(parts)
