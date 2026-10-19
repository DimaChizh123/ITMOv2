"""Compare model answers in lab/results/Q*.md with simple gold expectations.
Standard library only; writes lab/results/COMPARE.md.
"""
from __future__ import annotations
from pathlib import Path


def contains_any(text: str, needles: list[str]) -> bool:
    t = text.lower()
    return all(n.lower() in t for n in needles)


def main() -> None:
    root = Path(__file__).resolve().parent
    res = root / "results"
    report_lines = ["# Сравнение ответов", ""]

    # Q1: make test present
    q1 = (res / "Q1.md").read_text(encoding="utf-8", errors="ignore") if (res / "Q1.md").exists() else ""
    q1_ok = contains_any(q1, ["make test"]) and ("readme" in q1.lower() or "makefile" in q1.lower())
    report_lines.append(f"Q1: {'OK' if q1_ok else 'FAIL'}")

    # Q2: ValueError and empty name
    q2 = (res / "Q2.md").read_text(encoding="utf-8", errors="ignore") if (res / "Q2.md").exists() else ""
    q2_ok = contains_any(q2, ["valueerror", "empty name"]) or contains_any(q2, ["исключение", "empty name"]) 
    report_lines.append(f"Q2: {'OK' if q2_ok else 'FAIL'}")

    # Q3: unsubscribe отсутствует/нет
    q3 = (res / "Q3.md").read_text(encoding="utf-8", errors="ignore") if (res / "Q3.md").exists() else ""
    q3_ok = ("unsubscribe" in q3.lower()) and ("не" in q3.lower() or "нет" in q3.lower())
    report_lines.append(f"Q3: {'OK' if q3_ok else 'FAIL'}")

    # Q4: отсутствуют сведения о CI
    q4 = (res / "Q4.md").read_text(encoding="utf-8", errors="ignore") if (res / "Q4.md").exists() else ""
    q4_ok = ("ci" in q4.lower()) and ("нет" in q4.lower() or "отсутств" in q4.lower())
    report_lines.append(f"Q4: {'OK' if q4_ok else 'FAIL'}")

    # Q5: не сохраняются после перезапуска
    q5 = (res / "Q5.md").read_text(encoding="utf-8", errors="ignore") if (res / "Q5.md").exists() else ""
    q5_ok = ("не сохраня" in q5.lower()) or contains_any(q5, ["перезапуск", "не", "сохраня"])
    report_lines.append(f"Q5: {'OK' if q5_ok else 'FAIL'}")

    (res / "COMPARE.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
