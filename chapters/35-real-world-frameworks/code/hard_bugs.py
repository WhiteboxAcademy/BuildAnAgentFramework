"""Ten harder projects for chapter 35, in the same shape as chapter 34's bugs, so the same scoring works.

What makes each one hard is named in its "why". fix is a list of (file, old text, new text), since some need more than one change.
check_hard_bugs.py checks every visible test fails before the fix, and visible and hidden tests pass after it.
"""
import shutil
from pathlib import Path

BUGS = []


def bug(name, why, issue, files, tests, hidden, fix):
    BUGS.append({"name": name, "why": why, "issue": issue, "files": files, "tests": tests, "hidden": hidden, "fix": fix})


bug("receipt", "the cause is two files away from the failing test",
    "A £10.00 standard-rate item shows £210.00 on the receipt. It should be £12.00 with VAT at 20%.",
    {"receipt.py": '''from pricing import with_vat


def total(lines):
    """The receipt total in pounds: each line is (price, vat_kind)."""
    return round(sum(with_vat(price, kind) for price, kind in lines), 2)
''',
     "pricing.py": '''from vat import RATES


def with_vat(price, kind):
    """The price with VAT added."""
    return price * (1 + RATES[kind])
''',
     "vat.py": '''# VAT rates as fractions of the price.
RATES = {
    "standard": 20,
    "reduced": 0.05,
    "zero": 0,
}
'''},
    '''from receipt import total

def test_standard():
    assert total([(10.00, "standard")]) == 12.00
''',
    '''from receipt import total

def test_mixed():
    assert total([(10.00, "standard"), (10.00, "reduced"), (5.00, "zero")]) == 27.50
''',
    [("vat.py", '    "standard": 20,', '    "standard": 0.20,')])

bug("split", "the fix is new logic, not a changed line",
    "split_bill(10.00, 3) gives [3.33, 3.33, 3.33], which adds up to 9.99. The shares must add up to the bill exactly. "
    "Put any extra pennies on the first shares, so it should give [3.34, 3.33, 3.33].",
    {"bills.py": '''def split_bill(total, people):
    """Split a bill in pounds between people, as a list of shares in pounds."""
    share = round(total / people, 2)
    return [share] * people
'''},
    '''from bills import split_bill

def test_three():
    assert split_bill(10.00, 3) == [3.34, 3.33, 3.33]

def test_even():
    assert split_bill(9.00, 3) == [3.00, 3.00, 3.00]
''',
    '''from bills import split_bill

def test_adds_up():
    for total, people in [(10.00, 3), (100.00, 7), (0.05, 4), (19.99, 6)]:
        shares = split_bill(total, people)
        assert len(shares) == people
        assert round(sum(shares), 2) == total
        assert max(shares) - min(shares) <= 0.011
        assert shares == sorted(shares, reverse=True)
''',
    [("bills.py", '''    share = round(total / people, 2)
    return [share] * people''', '''    pennies = round(total * 100)
    share, extra = divmod(pennies, people)
    return [(share + (1 if i < extra else 0)) / 100 for i in range(people)]''')])

bug("weekly", "the test fails in the report, but the cause is in a date helper",
    "The weekly report's total is too low. It seems to miss a day each week.",
    {"report.py": '''from dates import week_days


def weekly_total(sales, monday):
    """Total sales for the week starting on monday. sales maps a date to a number."""
    return sum(sales.get(day, 0) for day in week_days(monday))
''',
     "dates.py": '''from datetime import timedelta


def week_days(monday):
    """The seven days of the week that starts on monday."""
    return [monday + timedelta(days=i) for i in range(6)]
'''},
    '''from datetime import date, timedelta
from report import weekly_total

def test_full_week():
    monday = date(2025, 3, 3)
    sales = {monday + timedelta(days=i): 10 for i in range(7)}
    assert weekly_total(sales, monday) == 70
''',
    '''from datetime import date
from dates import week_days

def test_days():
    days = week_days(date(2025, 3, 3))
    assert len(days) == 7 and days[-1] == date(2025, 3, 9)
''',
    [("dates.py", "range(6)", "range(7)")])

bug("cache", "the wrong price comes from a cache in another file, not from the price code",
    "price('tea', 'EUR') gives the pound price if price('tea', 'GBP') was asked for first.",
    {"prices.py": '''from cache import remember

POUNDS = {"tea": 2.50, "cake": 3.20}
RATES = {"GBP": 1.0, "EUR": 1.18}


@remember
def price(item, currency):
    """The price of an item in a currency."""
    return round(POUNDS[item] * RATES[currency], 2)
''',
     "cache.py": '''import functools


def remember(function):
    """Remember each answer, so asking again is quick."""
    answers = {}

    @functools.wraps(function)
    def remembered(*args):
        key = args[0]
        if key not in answers:
            answers[key] = function(*args)
        return answers[key]
    return remembered
'''},
    '''from prices import price

def test_both_currencies():
    assert price("tea", "GBP") == 2.50
    assert price("tea", "EUR") == 2.95
''',
    '''from cache import remember

def test_remember_uses_every_argument():
    calls = []
    @remember
    def add(a, b):
        calls.append((a, b))
        return a + b
    assert add(1, 2) == 3 and add(1, 5) == 6 and add(1, 2) == 3
    assert calls == [(1, 2), (1, 5)]
''',
    [("cache.py", "        key = args[0]", "        key = args")])

bug("duration", "the fix adds a feature: the code has no idea of seconds",
    "parse_duration('45s') crashes. Seconds should work, alone or with hours and minutes, such as '1h2m3s'.",
    {"durations.py": '''import re


def parse_duration(text):
    """Turn text such as '1h30m' or '2h' or '15m' into a number of seconds."""
    match = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?", text)
    hours, minutes = match.groups()
    return int(hours or 0) * 3600 + int(minutes or 0) * 60
'''},
    '''from durations import parse_duration

def test_old():
    assert parse_duration("1h30m") == 5400

def test_seconds():
    assert parse_duration("45s") == 45
''',
    '''from durations import parse_duration

def test_all():
    assert parse_duration("1h2m3s") == 3723
    assert parse_duration("2h") == 7200
    assert parse_duration("10m5s") == 605
''',
    [("durations.py", '''    match = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?", text)
    hours, minutes = match.groups()
    return int(hours or 0) * 3600 + int(minutes or 0) * 60''', '''    match = re.fullmatch(r"(?:(\\d+)h)?(?:(\\d+)m)?(?:(\\d+)s)?", text)
    hours, minutes, seconds = match.groups()
    return int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(seconds or 0)''')])

bug("restock", "one issue, two separate bugs in two functions",
    "Two problems with stock: restock('beans', 5) adds the 5 to the wrong item, and an item with exactly the "
    "warning level left isn't listed by low_stock().",
    {"stock.py": '''LEVELS = {"beans": 10, "milk": 4, "cups": 50}
WARN_AT = 5


def restock(item, amount):
    """Add amount to an item's stock."""
    for name in LEVELS:
        if name != item:
            LEVELS[name] += amount
            return


def low_stock():
    """Items at or below the warning level."""
    return sorted(name for name, level in LEVELS.items() if level < WARN_AT)
'''},
    '''import stock

def test_restock():
    stock.LEVELS.update(beans=10, milk=4, cups=50)
    stock.restock("beans", 5)
    assert stock.LEVELS == {"beans": 15, "milk": 4, "cups": 50}

def test_low_includes_the_warning_level():
    stock.LEVELS.update(beans=10, milk=5, cups=50)
    assert stock.low_stock() == ["milk"]
''',
    '''import stock

def test_more():
    stock.LEVELS.update(beans=2, milk=6, cups=5)
    stock.restock("cups", 1)
    assert stock.LEVELS == {"beans": 2, "milk": 6, "cups": 6}
    assert stock.low_stock() == ["beans"]
''',
    [("stock.py", "        if name != item:", "        if name == item:"),
     ("stock.py", "if level < WARN_AT)", "if level <= WARN_AT)")])

bug("tags", "the code looks right; the bug is Python's shared default list",
    "Tags from one order turn up on the next order.",
    {"orders.py": '''def new_order(item, tags=[]):
    """A new order with its tags."""
    tags.append("new")
    return {"item": item, "tags": tags}
'''},
    '''from orders import new_order

def test_separate_orders():
    first = new_order("tea")
    second = new_order("cake")
    assert first["tags"] == ["new"] and second["tags"] == ["new"]
''',
    '''from orders import new_order

def test_given_tags():
    assert new_order("tea", ["hot"])["tags"] == ["hot", "new"]
    assert new_order("cake")["tags"] == ["new"]
    assert new_order("pie")["tags"] == ["new"]
''',
    [("orders.py", '''def new_order(item, tags=[]):
    """A new order with its tags."""
    tags.append("new")''', '''def new_order(item, tags=None):
    """A new order with its tags."""
    tags = list(tags or [])
    tags.append("new")''')])

bug("leaderboard", "the order is wrong in a way that needs a two-part sort key",
    "On the leaderboard, players with equal scores should be listed A to Z by name. They come out Z to A.",
    {"board.py": '''def leaderboard(scores):
    """Names from the highest score to the lowest. scores maps a name to a score."""
    return sorted(scores, key=lambda name: (scores[name], name), reverse=True)
'''},
    '''from board import leaderboard

def test_ties_a_to_z():
    assert leaderboard({"Cleo": 5, "Ben": 7, "Asha": 5}) == ["Ben", "Asha", "Cleo"]
''',
    '''from board import leaderboard

def test_more():
    assert leaderboard({"d": 1, "c": 2, "b": 2, "a": 3}) == ["a", "b", "c", "d"]
''',
    [("board.py", "key=lambda name: (scores[name], name), reverse=True)", "key=lambda name: (-scores[name], name))")])

bug("mode", "a one-letter typo in a name read from the environment, in a different file from where it's used",
    "Setting QUILLON_MODE=test has no effect: the app always runs in live mode.",
    {"config.py": '''import os


def mode():
    """The mode the app runs in: live unless QUILLON_MODE says otherwise."""
    return os.environ.get("QUILON_MODE", "live")
''',
     "app.py": '''from config import mode


def banner():
    """The first line the app prints."""
    return f"Quillon till ({mode()} mode)"
'''},
    '''from app import banner

def test_test_mode(monkeypatch):
    monkeypatch.setenv("QUILLON_MODE", "test")
    assert banner() == "Quillon till (test mode)"
''',
    '''from config import mode

def test_default(monkeypatch):
    monkeypatch.delenv("QUILLON_MODE", raising=False)
    assert mode() == "live"
    monkeypatch.setenv("QUILLON_MODE", "demo")
    assert mode() == "demo"
''',
    [("config.py", 'os.environ.get("QUILON_MODE", "live")', 'os.environ.get("QUILLON_MODE", "live")')])


def _long_module():
    """A 40-function text helper module, 205 lines, with one bug in title_case at the end."""
    helpers = []
    for i, (name, body, doc) in enumerate([
        ("strip_all", "return [t.strip() for t in texts]", "Strip spaces from each text."),
        ("lower_all", "return [t.lower() for t in texts]", "Lower-case each text."),
        ("upper_all", "return [t.upper() for t in texts]", "Upper-case each text."),
        ("non_empty", "return [t for t in texts if t.strip()]", "Drop texts that are empty or only spaces."),
        ("longest", "return max(texts, key=len) if texts else ''", "The longest text."),
        ("shortest", "return min(texts, key=len) if texts else ''", "The shortest text."),
        ("total_length", "return sum(len(t) for t in texts)", "How many characters in all."),
        ("joined", "return ', '.join(texts)", "Join texts with commas."),
        ("first_letters", "return ''.join(t[:1] for t in texts)", "The first letter of each text."),
        ("dedupe", "return list(dict.fromkeys(texts))", "Drop repeats, keeping the first."),
    ]):
        helpers.append(f'def {name}(texts):\n    """{doc}"""\n    {body}\n')
    for i, (name, body, doc) in enumerate([
        ("count_vowels", "return sum(c in 'aeiou' for c in text.lower())", "How many vowels."),
        ("count_words", "return len(text.split())", "How many words."),
        ("reverse_words", "return ' '.join(reversed(text.split()))", "The words in reverse order."),
        ("squash_spaces", "return ' '.join(text.split())", "One space between words."),
        ("initials", "return ''.join(w[0].upper() for w in text.split())", "The first letter of each word."),
        ("is_shouting", "return text.isupper()", "True if every letter is a capital."),
        ("ends_sentence", "return text.rstrip().endswith(('.', '!', '?'))", "True if the text ends a sentence."),
        ("strip_punctuation", "return ''.join(c for c in text if c.isalnum() or c.isspace())", "Drop punctuation."),
        ("first_word", "return text.split()[0] if text.split() else ''", "The first word."),
        ("last_word", "return text.split()[-1] if text.split() else ''", "The last word."),
        ("shorten", "return text if len(text) <= 20 else text[:17] + '...'", "At most 20 characters."),
        ("pad_left", "return text.rjust(10)", "Pad to 10 characters on the left."),
        ("pad_right", "return text.ljust(10)", "Pad to 10 characters on the right."),
        ("centre", "return text.center(20)", "Centre in 20 characters."),
        ("mask", "return '*' * len(text)", "Hide every character."),
        ("mask_all_but_last4", "return '*' * max(len(text) - 4, 0) + text[-4:]", "Hide all but the last four characters."),
        ("is_palindrome", "t = strip_punctuation(text).lower().replace(' ', ''); return t == t[::-1]", "True if it reads the same backwards."),
        ("snake_case", "return '_'.join(text.lower().split())", "Words joined with underscores."),
        ("kebab_case", "return '-'.join(text.lower().split())", "Words joined with hyphens."),
        ("camel_case", "w = text.lower().split(); return w[0] + ''.join(x.title() for x in w[1:]) if w else ''", "Words joined in camelCase."),
        ("word_lengths", "return [len(w) for w in text.split()]", "The length of each word."),
        ("has_digit", "return any(c.isdigit() for c in text)", "True if any character is a digit."),
        ("digits_only", "return ''.join(c for c in text if c.isdigit())", "Just the digits."),
        ("letters_only", "return ''.join(c for c in text if c.isalpha())", "Just the letters."),
        ("swap_case", "return text.swapcase()", "Capitals to small letters and back."),
        ("repeat", "return ' '.join([text] * 3)", "The text three times."),
        ("quote", "return '\"' + text + '\"'", "The text in double quotes."),
        ("sentence_case", "return text[:1].upper() + text[1:].lower()", "A capital first letter, the rest small."),
        ("vowel_ratio", "return count_vowels(text) / len(text) if text else 0.0", "The share of characters that are vowels."),
    ]):
        helpers.append(f'def {name}(text):\n    """{doc}"""\n    {body}\n')
    title = '''SMALL_WORDS = {"a", "an", "and", "at", "for", "in", "of", "on", "or", "the", "to"}


def title_case(text):
    """Capitalise each word, except small words such as 'the' and 'of'. The first word is always capitalised."""
    words = text.lower().split()
    return " ".join(w if w in SMALL_WORDS else w.capitalize() for w in words)
'''
    return '"""Text helpers for menus, signs and receipts."""\n\n\n' + "\n\n".join(helpers) + "\n\n" + title


bug("signs", "one wrong line among 40 functions in a 205-line file (about 1,100 tokens)",
    "Shop signs come out as 'the Old Mill'. The first word of a title should always have a capital.",
    {"text_helpers.py": _long_module()},
    '''from text_helpers import title_case

def test_first_word():
    assert title_case("the old mill") == "The Old Mill"
''',
    '''from text_helpers import title_case, initials, snake_case

def test_more():
    assert title_case("a cup of tea") == "A Cup of Tea"
    assert title_case("tea and cake") == "Tea and Cake"
    assert initials("old mill") == "OM" and snake_case("Old Mill") == "old_mill"
''',
    [("text_helpers.py", '    return " ".join(w if w in SMALL_WORDS else w.capitalize() for w in words)',
      '    return " ".join(w if w in SMALL_WORDS and i > 0 else w.capitalize() for i, w in enumerate(words))')])


def make(bug, folder, fixed=False):
    """Write one project into folder: its files, tests/ and ISSUE.md. With fixed, apply the known fix."""
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "tests").mkdir(parents=True)
    for name, text in bug["files"].items():
        (folder / name).write_text(text)
    (folder / "tests" / f"test_{bug['name']}.py").write_text(bug["tests"])
    (folder / "ISSUE.md").write_text(f"# Bug report\n\n{bug['issue']}\n")
    if fixed:
        for name, old, new in bug["fix"]:
            text = (folder / name).read_text()
            assert text.count(old) == 1, (bug["name"], name, "fix doesn't match once")
            (folder / name).write_text(text.replace(old, new))
    return folder
