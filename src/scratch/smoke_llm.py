"""Manual smoke test for llm() (2.1). Loads the model, so run it yourself:

    uv run python src/scratch/smoke_llm.py
"""

from llm import llm


def main():
    print("== sampled (temperature=0.7) ==")
    print(llm("Summarize why a stock split doesn't change market cap."))

    print("\n== longer output (max_new_tokens=400) ==")
    print(llm("List 3 risks for AAPL.", max_new_tokens=400))

    print("\n== system steer + deterministic (temperature=0) ==")
    print(llm(
        "Classify the sentiment of: 'Apple beat earnings expectations.'",
        system="Respond with one word only: positive, negative, or neutral.",
        temperature=0,
    ))

    print("\n== determinism check (temperature=0 twice) ==")
    a = llm("List 3 risks for AAPL.", temperature=0)
    b = llm("List 3 risks for AAPL.", temperature=0)
    print("identical:", a == b)


if __name__ == "__main__":
    main()
