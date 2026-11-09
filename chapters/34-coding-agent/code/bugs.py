"""Twenty small projects, one bug each. Each has an issue, visible tests, hidden tests and the fix we know is right.

The agent sees the project and tests/. hidden/ is only used afterwards, to check a fix wasn't made to fit the visible tests alone.
"""
import shutil
from pathlib import Path

BUGS = []


def bug(name, issue, files, tests, hidden, fix):
    BUGS.append({"name": name, "issue": issue, "files": files, "tests": tests, "hidden": hidden, "fix": fix})


bug("average", "average([]) crashes with ZeroDivisionError. An empty list should give 0.",
    {"stats.py": '''def average(numbers):
    """The mean of a list of numbers."""
    return sum(numbers) / len(numbers)
'''},
    '''from stats import average

def test_average():
    assert average([2, 4, 6]) == 4

def test_empty():
    assert average([]) == 0
''',
    '''from stats import average

def test_more():
    assert average([1, 2]) == 1.5
    assert average([5]) == 5
    assert average([]) == 0
''',
    ("stats.py", "    return sum(numbers) / len(numbers)",
     "    if not numbers:\n        return 0\n    return sum(numbers) / len(numbers)"))

bug("pages", "Page 1 shows the second page of results. Pages are numbered from 1.",
    {"pages.py": '''def page(items, number, size=10):
    """One page of items. The first page is number 1."""
    start = number * size
    return items[start:start + size]
'''},
    '''from pages import page

def test_first_page():
    assert page(list(range(25)), 1) == list(range(10))

def test_last_page():
    assert page(list(range(25)), 3) == [20, 21, 22, 23, 24]
''',
    '''from pages import page

def test_sizes():
    assert page(list("abcdefg"), 2, size=3) == ["d", "e", "f"]
    assert page(list("abcdefg"), 1, size=3) == ["a", "b", "c"]
''',
    ("pages.py", "    start = number * size", "    start = (number - 1) * size"))

bug("leap", "is_leap(2000) says False, but 2000 was a leap year.",
    {"calendar_tools.py": '''def is_leap(year):
    """True if the year has a 29th of February."""
    return year % 4 == 0 and year % 100 != 0
'''},
    '''from calendar_tools import is_leap

def test_ordinary():
    assert is_leap(2024)
    assert not is_leap(2023)

def test_centuries():
    assert not is_leap(1900)
    assert is_leap(2000)
''',
    '''from calendar_tools import is_leap

def test_more():
    assert is_leap(2400)
    assert is_leap(1600)
    assert not is_leap(2100)
    assert is_leap(1996)
''',
    ("calendar_tools.py", "    return year % 4 == 0 and year % 100 != 0",
     "    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)"))

bug("words", "word_count counts too many words when there are two spaces in a row.",
    {"text.py": '''def word_count(text):
    """How many words are in the text."""
    return len(text.split(" "))
'''},
    '''from text import word_count

def test_simple():
    assert word_count("the cat sat") == 3

def test_double_space():
    assert word_count("the  cat sat") == 3
''',
    '''from text import word_count

def test_more():
    assert word_count("  hello   world  ") == 2
    assert word_count("one\\ttwo\\nthree") == 3
    assert word_count("") == 0
''',
    ("text.py", '    return len(text.split(" "))', "    return len(text.split())"))

bug("discount", "A 10% discount on 50.00 gives 0.00. It should give 45.00.",
    {"shop.py": '''def apply_discount(price, percent):
    """The price after taking off percent per cent."""
    return round(price - price * percent / 10, 2)
'''},
    '''from shop import apply_discount

def test_ten_percent():
    assert apply_discount(50.00, 10) == 45.00

def test_no_discount():
    assert apply_discount(20.00, 0) == 20.00
''',
    '''from shop import apply_discount

def test_more():
    assert apply_discount(80.00, 25) == 60.00
    assert apply_discount(19.99, 50) == 9.99 or apply_discount(19.99, 50) == 10.0
    assert apply_discount(100, 100) == 0
''',
    ("shop.py", "price * percent / 10,", "price * percent / 100,"))

bug("fahrenheit", "to_fahrenheit(100) gives 87.6. Water boils at 212 F.",
    {"temperature.py": '''def to_fahrenheit(celsius):
    """Celsius to Fahrenheit."""
    return celsius * 5 / 9 + 32
'''},
    '''from temperature import to_fahrenheit

def test_boiling():
    assert to_fahrenheit(100) == 212

def test_freezing():
    assert to_fahrenheit(0) == 32
''',
    '''from temperature import to_fahrenheit

def test_more():
    assert to_fahrenheit(-40) == -40
    assert to_fahrenheit(37) == 98.60000000000001 or round(to_fahrenheit(37), 1) == 98.6
''',
    ("temperature.py", "    return celsius * 5 / 9 + 32", "    return celsius * 9 / 5 + 32"))

bug("largest", "largest([-5, -2, -9]) gives 0, which isn't in the list.",
    {"maths.py": '''def largest(numbers):
    """The biggest number in a list that isn't empty."""
    best = 0
    for number in numbers:
        if number > best:
            best = number
    return best
'''},
    '''from maths import largest

def test_positive():
    assert largest([3, 9, 4]) == 9

def test_negative():
    assert largest([-5, -2, -9]) == -2
''',
    '''from maths import largest

def test_more():
    assert largest([-1]) == -1
    assert largest([-7, -3]) == -3
    assert largest([0, -1]) == 0
''',
    ("maths.py", "    best = 0", "    best = numbers[0]"))

bug("slug", "make_slug('Hello World') gives 'Hello-World'. Slugs should be lower case.",
    {"urls.py": '''def make_slug(title):
    """A title as a web address part: words joined by hyphens."""
    return "-".join(title.split())
'''},
    '''from urls import make_slug

def test_slug():
    assert make_slug("Hello World") == "hello-world"

def test_one_word():
    assert make_slug("news") == "news"
''',
    '''from urls import make_slug

def test_more():
    assert make_slug("  Big  NEWS Today ") == "big-news-today"
    assert make_slug("ABC") == "abc"
''',
    ("urls.py", '    return "-".join(title.split())', '    return "-".join(title.lower().split())'))

bug("stock", "Merging two stock counts loses items. merge({'pen': 2}, {'pen': 3}) should give {'pen': 5}.",
    {"stock.py": '''def merge(first, second):
    """Add two stock counts together."""
    total = dict(first)
    for item, count in second.items():
        total[item] = count
    return total
'''},
    '''from stock import merge

def test_merge_same():
    assert merge({"pen": 2}, {"pen": 3}) == {"pen": 5}

def test_merge_different():
    assert merge({"pen": 2}, {"ink": 1}) == {"pen": 2, "ink": 1}
''',
    '''from stock import merge

def test_more():
    assert merge({"a": 1, "b": 2}, {"b": 10, "c": 3}) == {"a": 1, "b": 12, "c": 3}
    first = {"a": 1}
    merge(first, {"a": 1})
    assert first == {"a": 1}
''',
    ("stock.py", "        total[item] = count", "        total[item] = total.get(item, 0) + count"))

bug("basket", "Every new basket starts with the items from the last basket.",
    {"basket.py": '''def add_item(item, basket=[]):
    """Add an item to a basket, or to a new basket if none is given."""
    basket.append(item)
    return basket
'''},
    '''from basket import add_item

def test_new_baskets_are_empty():
    assert add_item("apple") == ["apple"]
    assert add_item("pear") == ["pear"]

def test_existing_basket():
    assert add_item("b", ["a"]) == ["a", "b"]
''',
    '''from basket import add_item

def test_more():
    first = add_item("x")
    second = add_item("y")
    assert first == ["x"] and second == ["y"]
''',
    ("basket.py", 'def add_item(item, basket=[]):\n    """Add an item to a basket, or to a new basket if none is given."""\n',
     'def add_item(item, basket=None):\n    """Add an item to a basket, or to a new basket if none is given."""\n    if basket is None:\n        basket = []\n'))

bug("search", "find(items, x) says the last item isn't there, even when it is.",
    {"search.py": '''def find(items, target):
    """The position of target in a sorted list, or -1."""
    low, high = 0, len(items) - 1
    while low < high:
        middle = (low + high) // 2
        if items[middle] == target:
            return middle
        if items[middle] < target:
            low = middle + 1
        else:
            high = middle - 1
    return -1
'''},
    '''from search import find

def test_middle():
    assert find([1, 3, 5, 7, 9], 5) == 2

def test_last():
    assert find([1, 3, 5, 7, 9], 9) == 4

def test_missing():
    assert find([1, 3, 5], 4) == -1
''',
    '''from search import find

def test_more():
    assert find([4], 4) == 0
    assert find([1, 2], 2) == 1
    assert find([1, 2], 1) == 0
    assert find([], 1) == -1
    assert all(find(list(range(20)), n) == n for n in range(20))
''',
    ("search.py", "    while low < high:", "    while low <= high:"))

bug("minutes", "minutes('01:30') gives 130. It should give 90.",
    {"clock.py": '''def minutes(time):
    """How many minutes after midnight a time like '07:45' is."""
    hours, mins = time.split(":")
    return int(hours) * 100 + int(mins)
'''},
    '''from clock import minutes

def test_half_past_one():
    assert minutes("01:30") == 90

def test_midnight():
    assert minutes("00:00") == 0
''',
    '''from clock import minutes

def test_more():
    assert minutes("23:59") == 1439
    assert minutes("12:00") == 720
''',
    ("clock.py", "int(hours) * 100", "int(hours) * 60"))

bug("youngest", "by_age should put the youngest person first, but it puts the oldest first.",
    {"people.py": '''def by_age(people):
    """People sorted by age, youngest first. Each person is (name, age)."""
    return sorted(people, key=lambda person: person[1], reverse=True)
'''},
    '''from people import by_age

def test_order():
    people = [("Asha", 40), ("Ben", 12), ("Cleo", 25)]
    assert by_age(people) == [("Ben", 12), ("Cleo", 25), ("Asha", 40)]
''',
    '''from people import by_age

def test_more():
    assert by_age([("a", 3), ("b", 1), ("c", 2)]) == [("b", 1), ("c", 2), ("a", 3)]
    assert by_age([]) == []
''',
    ("people.py", ", reverse=True)", ")"))

bug("vowels", "count_vowels('APPLE') gives 0. Capital letters should count.",
    {"letters.py": '''def count_vowels(word):
    """How many vowels (a, e, i, o, u) are in the word."""
    return sum(1 for letter in word if letter in "aeiou")
'''},
    '''from letters import count_vowels

def test_lower():
    assert count_vowels("apple") == 2

def test_upper():
    assert count_vowels("APPLE") == 2
''',
    '''from letters import count_vowels

def test_more():
    assert count_vowels("Queue") == 4
    assert count_vowels("rhythm") == 0
    assert count_vowels("AeIoU") == 5
''',
    ("letters.py", "if letter in \"aeiou\")", "if letter.lower() in \"aeiou\")"))

bug("fizzbuzz", "fizzbuzz(15) gives 'Fizz'. It should give 'FizzBuzz'.",
    {"game.py": '''def fizzbuzz(n):
    """Fizz for multiples of 3, Buzz for 5, FizzBuzz for both, else the number."""
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    if n % 15 == 0:
        return "FizzBuzz"
    return str(n)
'''},
    '''from game import fizzbuzz

def test_fizz():
    assert fizzbuzz(9) == "Fizz"

def test_buzz():
    assert fizzbuzz(10) == "Buzz"

def test_both():
    assert fizzbuzz(15) == "FizzBuzz"
''',
    '''from game import fizzbuzz

def test_more():
    assert fizzbuzz(30) == "FizzBuzz"
    assert fizzbuzz(45) == "FizzBuzz"
    assert fizzbuzz(7) == "7"
    assert fizzbuzz(3) == "Fizz"
''',
    ("game.py", '''    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"
    if n % 15 == 0:
        return "FizzBuzz"''', '''    if n % 15 == 0:
        return "FizzBuzz"
    if n % 3 == 0:
        return "Fizz"
    if n % 5 == 0:
        return "Buzz"'''))

bug("invoice", "The invoice total ignores prices. Two items at 3.50 and one at 2.00 should total 9.00.",
    {"invoice.py": '''def total(lines):
    """The total of an invoice. Each line is (name, price, quantity)."""
    return round(sum(quantity for name, price, quantity in lines), 2)
'''},
    '''from invoice import total

def test_total():
    assert total([("tea", 3.50, 2), ("milk", 2.00, 1)]) == 9.00

def test_empty():
    assert total([]) == 0
''',
    '''from invoice import total

def test_more():
    assert total([("pen", 1.25, 4)]) == 5.00
    assert total([("a", 0.10, 3), ("b", 0.20, 1)]) == 0.50
''',
    ("invoice.py", "sum(quantity for", "sum(price * quantity for"))

bug("settings", "Setting debug = false in the settings file still turns debug mode on.",
    {"config.py": '''def parse_bool(text):
    """Turn 'true' or 'false' from a settings file into True or False."""
    return bool(text.strip())


def load(lines):
    """Read lines like 'debug = true' into a dict."""
    settings = {}
    for line in lines:
        key, value = line.split("=", 1)
        settings[key.strip()] = parse_bool(value)
    return settings
''',
     "app.py": '''from config import load


def debug_mode(lines):
    """True if the settings turn debug mode on."""
    return load(lines).get("debug", False)
'''},
    '''from app import debug_mode

def test_on():
    assert debug_mode(["debug = true"]) is True

def test_off():
    assert debug_mode(["debug = false"]) is False
''',
    '''from app import debug_mode
from config import load

def test_more():
    assert debug_mode(["debug = False"]) is False
    assert debug_mode(["debug = TRUE"]) is True
    assert load(["a = true", "b = false"]) == {"a": True, "b": False}
''',
    ("config.py", "    return bool(text.strip())", '    return text.strip().lower() == "true"'))

bug("inventory", "Taking more items than we have makes the stock negative. It should raise ValueError and leave the stock alone.",
    {"inventory.py": '''class Inventory:
    def __init__(self):
        self.counts = {}

    def add(self, item, count):
        self.counts[item] = self.counts.get(item, 0) + count

    def take(self, item, count):
        """Take items out. Raises ValueError if there aren't enough."""
        self.counts[item] = self.counts.get(item, 0) - count
''',
     "orders.py": '''from inventory import Inventory


def fill(inventory, order):
    """Take every (item, count) in an order out of the inventory."""
    for item, count in order:
        inventory.take(item, count)
'''},
    '''import pytest
from inventory import Inventory
from orders import fill

def test_take():
    stock = Inventory()
    stock.add("bolt", 5)
    fill(stock, [("bolt", 3)])
    assert stock.counts["bolt"] == 2

def test_too_many():
    stock = Inventory()
    stock.add("bolt", 2)
    with pytest.raises(ValueError):
        stock.take("bolt", 3)
    assert stock.counts["bolt"] == 2
''',
    '''import pytest
from inventory import Inventory

def test_more():
    stock = Inventory()
    with pytest.raises(ValueError):
        stock.take("nut", 1)
    stock.add("nut", 4)
    stock.take("nut", 4)
    assert stock.counts["nut"] == 0
''',
    ("inventory.py", "        self.counts[item] = self.counts.get(item, 0) - count",
     "        if self.counts.get(item, 0) < count:\n            raise ValueError(f\"not enough {item}\")\n        self.counts[item] = self.counts.get(item, 0) - count"))

bug("nights", "A booking from the 1st to the 3rd is charged for 3 nights. It's 2 nights.",
    {"booking.py": '''from datetime import date


def nights(arrive, leave):
    """How many nights a stay is."""
    return (leave - arrive).days + 1


def price(arrive, leave, per_night):
    return nights(arrive, leave) * per_night
'''},
    '''from datetime import date
from booking import nights, price

def test_two_nights():
    assert nights(date(2026, 5, 1), date(2026, 5, 3)) == 2

def test_price():
    assert price(date(2026, 5, 1), date(2026, 5, 2), 80) == 80
''',
    '''from datetime import date
from booking import nights

def test_more():
    assert nights(date(2026, 1, 30), date(2026, 2, 2)) == 3
    assert nights(date(2026, 6, 1), date(2026, 6, 8)) == 7
''',
    ("booking.py", "    return (leave - arrive).days + 1", "    return (leave - arrive).days"))

bug("password", "A password of exactly 8 characters is rejected. 8 is the minimum, so it should be allowed.",
    {"accounts.py": '''def strong_enough(password):
    """At least 8 characters, with at least one digit."""
    return len(password) > 8 and any(c.isdigit() for c in password)
'''},
    '''from accounts import strong_enough

def test_eight():
    assert strong_enough("abcdefg1")

def test_short():
    assert not strong_enough("abc1")

def test_no_digit():
    assert not strong_enough("abcdefghij")
''',
    '''from accounts import strong_enough

def test_more():
    assert not strong_enough("abcdef1")
    assert strong_enough("12345678")
    assert not strong_enough("")
''',
    ("accounts.py", "len(password) > 8", "len(password) >= 8"))


def make(bug, folder, fixed=False):
    """Write one project into folder: its files, tests/ and an issue. hidden/ is kept elsewhere."""
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    (folder / "tests").mkdir(parents=True)
    for name, text in bug["files"].items():
        (folder / name).write_text(text)
    (folder / "tests" / f"test_{bug['name']}.py").write_text(bug["tests"])
    (folder / "ISSUE.md").write_text(f"# Bug report\n\n{bug['issue']}\n")
    if fixed:
        name, old, new = bug["fix"]
        text = (folder / name).read_text()
        assert text.count(old) == 1, (bug["name"], "fix doesn't match once")
        (folder / name).write_text(text.replace(old, new))
    return folder
