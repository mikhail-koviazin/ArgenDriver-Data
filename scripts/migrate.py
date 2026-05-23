#!/usr/bin/env python3
"""One-time migration: splits questions.json + copies images into per-question folders."""

import json
import os
import shutil
import re

ROOT = os.path.join(os.path.dirname(__file__), "..")
SRC_QUESTIONS = os.path.join(ROOT, "..", "ArgenDriver", "app", "questions.json")
SRC_IMAGES = os.path.join(ROOT, "..", "ArgenDriver", "app", "screens", "TestScreen", "question_images")
QUESTIONS_DIR = os.path.join(ROOT, "questions")

with open(SRC_QUESTIONS, encoding="utf-8") as f:
    questions = json.load(f)

copied_images = 0
skipped_images = 0

for index, question in enumerate(questions):
    folder = os.path.join(QUESTIONS_DIR, f"{index:04d}")
    os.makedirs(folder, exist_ok=True)

    # Write question.json (without the 'num' field — it will be the folder index)
    q_data = {k: v for k, v in question.items() if k != "num"}
    with open(os.path.join(folder, "question.json"), "w", encoding="utf-8") as f:
        json.dump(q_data, f, ensure_ascii=False, indent=2)

    # Copy image if present
    if question.get("img"):
        m = re.search(r"(b\d+)\.jpg", question["img"], re.IGNORECASE)
        if m:
            image_key = m.group(1)
            src_path = os.path.join(SRC_IMAGES, f"{image_key}.jpg")
            if os.path.exists(src_path):
                shutil.copy2(src_path, os.path.join(folder, f"{image_key}.jpg"))
                copied_images += 1
            else:
                print(f"  WARNING: image not found locally: {image_key}.jpg (question index {index})")
                skipped_images += 1

print(f"Done: {len(questions)} questions, {copied_images} images copied, {skipped_images} skipped")
