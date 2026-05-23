#!/usr/bin/env python3
"""
apply_fixes.py — Apply all translation fixes from the audit report.

Fixes:
  - Swapped EN/RU translations between response pairs
  - Cyclically shifted EN/RU translations (3-way rotations)
  - Individual text errors (wrong words, embedded foreign text, opposite meanings)
  - Contradictory explanations

Run: python scripts/apply_fixes.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
QUESTIONS_DIR = ROOT / "questions"


def load(folder: str) -> dict:
    p = QUESTIONS_DIR / folder / "question.json"
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(folder: str, data: dict) -> None:
    p = QUESTIONS_DIR / folder / "question.json"
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  saved {folder}")


def swap_responses(q: dict, i: int, j: int) -> None:
    """Swap EN and RU translations between responses[i] and responses[j]."""
    ri, rj = q["responses"][i]["text"], q["responses"][j]["text"]
    ri["en"], rj["en"] = rj["en"], ri["en"]
    ri["ru"], rj["ru"] = rj["ru"], ri["ru"]


def rotate_left(q: dict, indices: list[int]) -> None:
    """Left-rotate EN and RU: new[0]=old[1], new[1]=old[2], new[2]=old[0]."""
    n = len(indices)
    saved_en = [q["responses"][i]["text"]["en"] for i in indices]
    saved_ru = [q["responses"][i]["text"]["ru"] for i in indices]
    for k, i in enumerate(indices):
        q["responses"][i]["text"]["en"] = saved_en[(k + 1) % n]
        q["responses"][i]["text"]["ru"] = saved_ru[(k + 1) % n]


def rotate_right(q: dict, indices: list[int]) -> None:
    """Right-rotate EN and RU: new[0]=old[-1], new[1]=old[0], new[2]=old[1]."""
    n = len(indices)
    saved_en = [q["responses"][i]["text"]["en"] for i in indices]
    saved_ru = [q["responses"][i]["text"]["ru"] for i in indices]
    for k, i in enumerate(indices):
        q["responses"][i]["text"]["en"] = saved_en[(k - 1) % n]
        q["responses"][i]["text"]["ru"] = saved_ru[(k - 1) % n]


# ── SWAP CASES ────────────────────────────────────────────────────────────────

SWAPS: list[tuple[str, int, int]] = [
    # folder, response_index_A, response_index_B
    ("0022", 0, 1),
    ("0043", 0, 1),
    ("0046", 0, 1),
    ("0058", 0, 1),
    ("0073", 0, 1),
    ("0084", 0, 1),
    ("0094", 0, 1),
    ("0095", 0, 2),
    ("0096", 0, 2),
    ("0101", 0, 1),
    ("0103", 0, 1),
    ("0104", 0, 1),
    ("0116", 0, 1),
    ("0140", 0, 1),
    ("0148", 0, 1),
    ("0154", 0, 1),
    ("0156", 0, 1),
    ("0172", 0, 1),
    ("0190", 1, 2),
    ("0205", 0, 1),
    ("0212", 0, 1),
    ("0222", 0, 1),
    ("0237", 0, 1),
    ("0282", 0, 1),
    ("0287", 0, 1),
    ("0296", 0, 1),
    ("0306", 0, 1),
    ("0318", 0, 1),
    ("0330", 0, 1),
    ("0335", 0, 1),
    ("0341", 0, 1),
    ("0342", 0, 1),
    ("0350", 0, 1),
    ("0353", 0, 1),
    ("0358", 0, 1),
    ("0360", 0, 1),
    ("0378", 0, 1),
    ("0407", 0, 1),
    ("0420", 0, 1),
    ("0432", 0, 1),
    ("0438", 0, 1),
    ("0455", 1, 2),
]


def apply_swaps() -> None:
    for folder, i, j in SWAPS:
        q = load(folder)
        swap_responses(q, i, j)
        save(folder, q)


# ── CYCLIC ROTATION CASES ─────────────────────────────────────────────────────

def apply_rotations() -> None:
    # Q0034: right rotation [0,1,2] → new[0]=old[2], new[1]=old[0], new[2]=old[1]
    # EN[0]="right edge"(→ES[1]), EN[1]="left edge"(→ES[2]), EN[2]="can't circulate"(→ES[0])
    # Desired: EN[0]=translate(ES[0])=old[2], EN[1]=translate(ES[1])=old[0], EN[2]=translate(ES[2])=old[1]
    q = load("0034")
    rotate_right(q, [0, 1, 2])
    save("0034", q)

    # Q0123: left rotation [0,1,2] → new[0]=old[1], new[1]=old[2], new[2]=old[0]
    # EN[0]="coordination/attention"(→ES[2]), EN[1]="high concentration"(→ES[0]), EN[2]="no, reduced"(→ES[1])
    # Desired: EN[0]=old[1], EN[1]=old[2], EN[2]=old[0]
    q = load("0123")
    rotate_left(q, [0, 1, 2])
    save("0123", q)

    # Q0315: left rotation [0,1,2]
    # EN[0]="hazard lights"(→ES[2]), EN[1]="turn signal entering side"(→ES[0]), EN[2]="opposite side"(→ES[1])
    # Desired: EN[0]=old[1], EN[1]=old[2], EN[2]=old[0]
    q = load("0315")
    rotate_left(q, [0, 1, 2])
    save("0315", q)

    # Q0371: right rotation [0,1,2]
    # EN[0]="inside out and outside in"(→ES[1]), EN[1]="windshield only"(→ES[2]), EN[2]="only inside out"(→ES[0])
    # Desired: EN[0]=old[2], EN[1]=old[0], EN[2]=old[1]
    q = load("0371")
    rotate_right(q, [0, 1, 2])
    save("0371", q)


# ── INDIVIDUAL TEXT FIXES ─────────────────────────────────────────────────────

def apply_individual_fixes() -> None:
    # Q0009: "Visión Cero" mistranslated as "Нулевая видимость" (Zero Visibility)
    # Correct: "Нулевое видение" (Vision Zero)
    q = load("0009")
    q["text"]["ru"] = q["text"]["ru"].replace("Нулевая видимость", "Нулевое видение")
    q["explanation"]["text"]["ru"] = q["explanation"]["text"]["ru"].replace(
        "Нулевая видимость", "Нулевое видение"
    )
    save("0009", q)

    # Q0044: Polish word "chwilę" embedded in Russian text
    q = load("0044")
    q["responses"][0]["text"]["ru"] = q["responses"][0]["text"]["ru"].replace(
        "на chwilę", "на момент"
    )
    save("0044", q)

    # Q0099: "En ningún caso" → opposite meaning in EN/RU
    q = load("0099")
    q["responses"][2]["text"]["en"] = "In no case."
    q["responses"][2]["text"]["ru"] = "Ни в коем случае."
    save("0099", q)

    # Q0106: English phrase in Russian question + wrong word in explanation
    q = load("0106")
    q["text"]["ru"] = (
        "Какой из следующих вариантов непосредственно связан "
        "с предотвращением и снижением дорожно-транспортных происшествий?"
    )
    q["explanation"]["text"]["ru"] = q["explanation"]["text"]["ru"].replace(
        "оставаться настойчивым", "оставаться бдительным"
    )
    save("0106", q)

    # Q0139: English word "Concentration" not translated in RU explanation
    q = load("0139")
    q["explanation"]["text"]["ru"] = q["explanation"]["text"]["ru"].replace(
        "повышает Concentration водителя", "повышает концентрацию водителя"
    )
    save("0139", q)

    # Q0158: Explanation contradicts correct answer (Falso)
    # Statement: "Agents can ONLY detain vehicles WITH police" → Falso = they can do it independently
    q = load("0158")
    q["explanation"]["text"]["es"] = (
        "Los Agentes de Tránsito pueden proceder a la detención de un vehículo "
        "de manera autónoma, sin necesidad de personal policial."
    )
    q["explanation"]["text"]["en"] = (
        "Traffic Agents can proceed to the detention of a vehicle independently, "
        "without the need for police personnel."
    )
    q["explanation"]["text"]["ru"] = (
        "Сотрудники дорожного движения могут задерживать транспортные средства "
        "самостоятельно, без присутствия полицейских."
    )
    save("0158", q)

    # Q0192: English phrase "Repeatedly honking the horn" in Russian response
    q = load("0192")
    q["responses"][1]["text"]["ru"] = q["responses"][1]["text"]["ru"].replace(
        "Repeatedly honking the horn", "неоднократно сигналя клаксоном"
    )
    # Fix comma spacing too
    q["responses"][1]["text"]["ru"] = q["responses"][1]["text"]["ru"].replace(
        "автомобиля,Repeatedly", "автомобиля, Repeatedly"
    ).replace(
        "автомобиля, неоднократно", "автомобиля, неоднократно"
    )
    save("0192", q)

    # Q0204: "vehículos de transporte de pasajero" mistranslated as "Грузовые автомобили"
    q = load("0204")
    q["responses"][0]["text"]["ru"] = "Транспортные средства для перевозки пассажиров."
    save("0204", q)

    # Q0260: Explanation says 20 km/h but correct answer is 30 km/h
    q = load("0260")
    q["explanation"]["text"]["es"] = (
        "La velocidad máxima en este tramo cercano a un establecimiento escolar "
        "es de 30 km/h, según la señalización indicada."
    )
    q["explanation"]["text"]["en"] = (
        "The maximum speed in this section near a school is 30 km/h, "
        "as indicated by the road sign."
    )
    q["explanation"]["text"]["ru"] = (
        "Максимально допустимая скорость на этом участке вблизи школы "
        "составляет 30 км/ч, согласно установленному дорожному знаку."
    )
    save("0260", q)

    # Q0385: "направленность торможения" should be "направленную устойчивость"
    q = load("0385")
    q["responses"][2]["text"]["ru"] = q["responses"][2]["text"]["ru"].replace(
        "направленность торможения", "направленную устойчивость"
    )
    save("0385", q)

    # Q0406: Japanese/Chinese characters "最高危险" in Russian text
    q = load("0406")
    q["responses"][2]["text"]["ru"] = "Пешеходный переход с максимальной опасностью."
    save("0406", q)

    # Q0437: "What is" → "That it is" (responses should complete the question stem)
    q = load("0437")
    q["responses"][0]["text"]["en"] = "That it is a preferential lane for cyclists."
    q["responses"][1]["text"]["en"] = "That it is a lane exclusively for cyclists."
    save("0437", q)

    # Q0447: "Начало полудороги" → "Начало полуавтострады" (semiautopista)
    q = load("0447")
    q["responses"][2]["text"]["ru"] = "Начало полуавтострады."
    save("0447", q)

    # Q0448: "Конец полупаводного пути" → "Конец полуавтострады"
    q = load("0448")
    q["responses"][0]["text"]["ru"] = "Конец полуавтострады."
    save("0448", q)


def main() -> None:
    print("Applying swap fixes...")
    apply_swaps()
    print("\nApplying rotation fixes...")
    apply_rotations()
    print("\nApplying individual text fixes...")
    apply_individual_fixes()
    print(f"\nDone. {len(SWAPS)} swaps + 4 rotations + 14 individual fixes applied.")


if __name__ == "__main__":
    main()
