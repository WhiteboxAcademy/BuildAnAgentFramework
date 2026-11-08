"""Print our saved runs. usage: python3 read_results.py teams|tools|batch|relay|review|logs|runaway

For logs, you can add one count: late, ran-out or baked.
"""
import json
import sys

saved = json.load(open("results/chapter30.json"))
part = sys.argv[1]

if part == "teams":
    print(f"{'Setup':<22}{'Of 126':>7}{'Calls':>7}{'Tokens in':>11}{'Seconds':>9}")
    for row in saved["teams"]:
        print(f"{row['setup']:<22}{row['passed']:>7}{row['calls']:>7}{row['tokens_in']:>11,}{row['seconds']:>9}")
elif part == "tools":
    print(f"{'Setup':<33}{'Right':>6}{'Wrong':>6}{'None':>5}{'Calls':>6}{'Read at most':>13}")
    for row in saved["tools"]:
        print(f"{row['setup']:<33}{row['right']:>6}{row['wrong']:>6}{row['none']:>5}{row['calls']:>6}{row['read_max']:>13,}")
elif part == "batch":
    print(f"{'In one chat':<12}{'Window':>8}{'Right':>6}{'Of':>5}{'Calls':>6}")
    for row in saved["batch"]:
        print(f"{row['size']:<12}{row['window']!s:>8}{row['passed']:>6}{row['asked']:>5}{row['calls']:>6}")
elif part == "relay":
    print(f"{'Setup':<22}{'Five passes, of 30':<20}{'Of 150':>6}{'Calls per pass':>16}")
    for row in saved["relay"]:
        passes = " ".join(f"{count:>2}" for count in row["passes"])
        print(f"{row['setup']:<22}{passes:<20}{sum(row['passes']):>6}{sum(row['calls']) // 5:>16}")
elif part == "review":
    print(f"{'Setup':<16}{'Of 126':>7}{'Fixed':>6}{'Broke':>6}{'Extra calls':>12}")
    for name, row in saved["review"].items():
        fixed, broke = (row["fixed"], row["broke"]) if name != "first" else ("-", "-")
        print(f"{name:<16}{row['passed']:>7}{fixed:>6}{broke:>6}{row['calls']:>12}")
elif part == "logs":
    print("How far off each try was, on average across the four branches")
    print(f"{'Count':<9}{'Setup':<28}Off by")
    for row in saved["logs"]:
        if len(sys.argv) > 2 and row["measure"] != sys.argv[2]:
            continue
        print(f"{row['measure']:<9}{row['setup']:<28}{', '.join(f'{error:.0%}' for error in row['errors'])}")
elif part == "runaway":
    run = saved["runaway"]
    print("Question:", run["question"])
    print(f"Tokens written: {run['tokens_out']:,}")
    print("Start:", run["answer"][:150])
    print("End:  ", run["answer"][-150:])
