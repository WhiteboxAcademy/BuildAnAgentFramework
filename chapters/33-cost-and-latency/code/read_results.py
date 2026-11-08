"""Print our saved runs. usage: python3 read_results.py breakdown|less|cost|parallel|stream|cache"""
import json
import sys

saved = json.load(open("results/chapter33.json"))
part = sys.argv[1]

if part == "breakdown":
    short = {"system prompt": "system", "tool descriptions": "tools", "question": "question", "tool results": "results",
             "model's own turns": "own turns"}
    print("Share of everything sent, one pass of 42 questions")
    print(f"{'':<23}" + "".join(f"{label:>11}" for label in short.values()))
    for row in saved["breakdown"]:
        print(f"{row['model']:<23}" + "".join(f"{row['parts'][name]:>11.0%}" for name in short))
    print("system = system prompt, tools = tool descriptions, results = tool results,")
    print("own turns = the model's earlier turns")
    for row in saved["breakdown"]:
        print(f"{row['model']}: model {row['model_seconds']:.0f} s, tools {row['tool_seconds']:.0f} s, of {row['wall_seconds']:.0f} s")
elif part == "less":
    print("qwen2.5:7b, three passes of 42. k is search results per search, size is words per chunk")
    print(f"{'Setup':<16}{'Right':>7}{'Tokens in':>11}{'Seconds':>9}")
    for row in saved["less_local"]:
        print(f"{row['setup']:<16}{row['passed']:>4}/{row['runs']:<3}{row['tokens_in']:>10,}{row['wall_seconds']:>9.0f}")
elif part == "cost":
    print("gemini-3.1-flash-lite, one pass of 42, chunks of 60 words")
    print(f"{'Setup':<7}{'Right':>7}{'Tokens in':>11}{'Cost':>9}{'Per right answer':>18}")
    for row in saved["less_cloud"]:
        print(f"{row['setup']:<7}{row['passed']:>4}/{row['runs']:<3}{row['tokens_in']:>10,}{'$' + format(row['dollars'], '.4f'):>9}"
              f"{'$' + format(row['per_correct'], '.6f'):>18}")
elif part == "parallel":
    print(f"{'Model':<24}{'At once':>8}{'Right':>7}{'Seconds':>9}")
    for model, rows in saved["parallel"].items():
        for row in rows:
            print(f"{model:<24}{row['workers']:>8}{row['passed']:>4}/{row['of']}{row['seconds']:>9.0f}")
elif part == "stream":
    print(f"{'Model':<24}{'First words':>12}{'Whole reply':>13}")
    for model, rows in saved["stream"].items():
        for row in rows:
            print(f"{model:<24}{row['first_words']:>11.2f}s{row['whole_reply']:>12.2f}s")
elif part == "cache":
    print("The 40 tools from chapter 30, 6,569 tokens, sent five times")
    print(f"{'Model':<24}{'From cache, each try':<30}")
    for model, rows in saved["cache"].items():
        print(f"{model:<24}{'  '.join(f'{row['cached']:,}' for row in rows)}")
