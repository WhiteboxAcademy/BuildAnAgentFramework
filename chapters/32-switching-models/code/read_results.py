"""Print our saved runs. usage: python3 read_results.py eval|tools|attacks|spend"""
import json
import sys

saved = json.load(open("results/chapter32.json"))
part = sys.argv[1]

if part == "eval":
    print(f"{'Model':<30}{'Passed':>10}{'Calls':>7}{'Seconds':>9}{'Empty':>7}{'Thai or Chinese':>17}{'Step limit':>12}")
    for row in saved["eval"]:
        passed = f"{row['passed']}/{row['runs']}"
        print(f"{row['setup']:<30}{passed:>10}{row['calls']:>7}{row['seconds']:>9}{row['empty']:>7}{row['not_english']:>17}"
              f"{row['step_limit']:>12}")
elif part == "tools":
    print(f"{'Model':<24}{'All 40 tools':>13}{'Router':>8}{'Of':>5}")
    for row in saved["tools"]:
        print(f"{row['model']:<24}{row['all_40']:>13}{row['router']:>8}{row['tries']:>5}")
elif part == "attacks":
    print("Chapter 31's four attacks, with no defence: times the payroll code was emailed out")
    for row in saved["attacks"]:
        print(f"  {row['model']:<24}{row['leaked']:>3} of {row['runs']}")
elif part == "spend":
    print("Google's paid prices on 2026-11-08, dollars per million tokens")
    for name, (price_in, price_out) in saved["prices"].items():
        print(f"  {name:<24}in {price_in:.2f}  out {price_out:.2f}")
    print(f"Everything we sent to Gemini for this chapter: ${saved['spent']:.2f}")
