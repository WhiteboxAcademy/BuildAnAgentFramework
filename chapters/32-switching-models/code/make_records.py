"""Provided: writes a year of invented Quillon Coffee records into workspace/records."""
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).parent / "workspace" / "records"
STAFF = ["Aisha", "Ben", "Carla", "Dev", "Elif", "Finn", "Grace", "Hugo", "Isla", "Jonas", "Kira", "Leo", "Maya", "Nico"]
BRANCHES = {
    "harbour": [0, 1, 2, 3, 4, 5, 6],
    "riverside": [0, 1, 2, 3, 4, 5, 6],
    "station": [0, 1, 2, 3, 4, 5, 6],
    "old-mill": [1, 2, 3, 4, 5, 6],
}
WEATHER = ["Bright and cold", "Light rain all day", "Mild and grey", "Windy", "Sunny", "Heavy showers", "Warm", "Foggy start"]
PACE = ["Steady morning, quiet after lunch.", "Busy from the first hour.", "Slow day overall.", "Queue out of the door at lunch.",
        "Quiet until the school run.", "Good trade all afternoon."]
NOTES = [
    "{a} restocked the takeaway lids and cups.", "{a} deep cleaned the pastry cabinet.", "Till balanced to the penny.",
    "Till was £{small} over, recorded on the cash sheet.", "Ran out of {item} by {time}.", "{a} covered {b}'s break.",
    "A regular asked about the {item} again.", "{a} practised latte art with the spare milk.", "Delivery arrived on time and matched the note.",
    "Dairy delivery was {mins} minutes late.", "Two pastries went on the waste sheet.", "{a} changed the water filter reminder in StaffHub.",
    "Grinder needed a small adjustment after the morning rush.", "Fridge log completed at opening and at 14:00.",
    "{a} helped a customer with the loyalty app.", "Swept the outdoor area twice because of leaves.", "Printer roll replaced on till two.",
    "{a} updated the chalkboard with this week's filter coffee.", "Lost property box checked, nothing to report.",
    "A customer returned a scarf left yesterday.", "{a} and {b} rearranged the retail shelf.", "Bins collected as normal.",
]
ITEMS = ["almond croissants", "seeded flapjacks", "oat milk", "cheese scones", "banana bread", "lemon drizzle", "soya milk", "cinnamon buns"]
PLANTED = {
    ("harbour", date(2025, 2, 11)): "Storm surge flooded the Harbour cellar overnight. Stock worth £640 was lost, mostly paper cups and syrups. Lena Ortiz arranged a dry-out with Brinley Restoration.",
    ("riverside", date(2025, 6, 19)): "The guest at the cupping club tonight was Anika Voss, a green coffee buyer, who led a tasting of washed Ethiopian lots.",
    ("old-mill", date(2025, 8, 7)): "A film crew used the gallery for a morning and paid £350 for the location. Ravi Nair put the money towards new gallery lighting.",
    ("station", date(2025, 12, 23)): "The card reader on till one failed at 07:40 and stayed down until 11:15. We took cash only on that till and lost roughly £300 of trade.",
    ("harbour", date(2025, 9, 3)): "Pernille Lund from the ferry company agreed a standing order of 40 flat whites for the Saturday crew breakfast.",
    ("station", date(2025, 4, 16)): "Concourse fire drill closed the unit for 35 minutes from 10:05. No trade during that time.",
}
SUPPLIERS = {
    "Greywell Dairy": ("Milk and cream", "Hannah Pryce", "No minimum order", "30 days"),
    "Fennel Bakehouse": ("Pastries and cakes", "Oskar Lind", "Minimum order £60 per branch", "14 days"),
    "Tidewater Espresso Service": ("Machine service, Harbour and Old Mill", "Marek Dolan", "Call-out fee £85", "30 days"),
    "Northline Service": ("Machine service, Riverside and Station", "Yusuf Kaya", "Call-out fee £95", "30 days"),
    "GreenLoop": ("Coffee grounds collection", "Tess Moreau", "Fixed monthly fee of £48 per branch", "30 days"),
    "Halden Pest Control": ("Pest control", "Colm Reilly", "Fixed fee of £70 per visit", "30 days"),
    "SecureRoute": ("Cash collection", "Dara Quinn", "Fixed fee of £22 per collection", "14 days"),
    "Marlow Paper Goods": ("Cups, lids and napkins", "Sofia Bell", "Minimum order 10 cases", "45 days"),
}
PRODUCTS = {
    "beans": [("Lantern 250g", "£8.50", "House blend from Brazil and Colombia, with notes of milk chocolate."),
              ("Lantern 1kg", "£29.00", "House blend, wholesale size."),
              ("Dusk decaf 250g", "£9.25", "Sugarcane-process decaf from Colombia, with notes of caramel."),
              ("Harvest Ethiopia 250g", "£11.00", "Washed Yirgacheffe with notes of bergamot."),
              ("Harvest Guatemala 250g", "£10.50", "Honey process, with notes of red apple.")],
    "bakery": [("Almond croissant", "£3.60", "Contains nuts, gluten, egg and milk."), ("Seeded flapjack", "£3.10", "Contains sesame, nuts and gluten."),
               ("Cheese scone", "£3.20", "Contains gluten, egg and milk."), ("Cinnamon bun", "£3.40", "Contains gluten, egg and milk.")],
    "drinks": [("Flat white", "£3.70", "Double shot with 150ml of milk."), ("Cortado", "£3.30", "Double shot with 60ml of milk."),
               ("Filter coffee", "£3.20", "Changes weekly."), ("Hot chocolate", "£3.80", "Made with whole milk.")],
    "kit": [("Quillon travel cup", "£14.00", "350ml, stainless steel."), ("Hand grinder", "£38.00", "Ceramic burrs."),
            ("Pour-over starter set", "£32.00", "Dripper, filters and 250g of Lantern.")],
}


def entry(rng, day):
    a, b = rng.sample(STAFF, 2)
    values = {"a": a, "b": b, "item": rng.choice(ITEMS), "small": rng.randint(1, 4), "mins": rng.randint(10, 40),
              "time": f"{rng.randint(11, 15)}:{rng.choice(['00', '15', '30', '45'])}"}
    notes = " ".join(note.format(**values) for note in rng.sample(NOTES, rng.randint(2, 3)))
    return f"{rng.choice(WEATHER)}. {rng.choice(PACE)} {notes}"


def write_logs(rng):
    for branch, days in BRANCHES.items():
        for month in range(1, 13):
            title = date(2025, month, 1).strftime("%B %Y")
            lines = [f"# {branch.title()} branch log, {title}"]
            day = date(2025, month, 1)
            while day.month == month:
                if day.weekday() in days:
                    text = entry(rng, day)
                    if (branch, day) in PLANTED:
                        text = f"{PLANTED[(branch, day)]} {text}"
                    lines.append(f"## {day.strftime('%A')} {day.day} {title}\n\n{text}")
                day += timedelta(days=1)
            (OUT / f"log-{branch}-2025-{month:02}.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")


def write_sheets():
    lines = ["# Suppliers"]
    for name, (supplies, contact, terms, payment) in SUPPLIERS.items():
        lines.append(f"## {name}\n\nSupplies: {supplies}. Account manager: {contact}. Terms: {terms}. Invoices are paid within {payment}.")
    (OUT / "suppliers.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    for group, rows in PRODUCTS.items():
        lines = [f"# Product sheet: {group}"]
        lines += [f"## {name}\n\nPrice: {price}. {detail}" for name, price, detail in rows]
        (OUT / f"products-{group}.md").write_text("\n\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    write_logs(random.Random(2025))
    write_sheets()
