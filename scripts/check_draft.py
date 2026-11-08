#!/usr/bin/env python3
"""Mechanical checks for one email draft, compared against the other drafts in its folder.

Usage: check_draft.py <draft.md>   (exit 0 = pass, 1 = rewrite and run again)
       check_draft.py --selftest
"""
import re
import shutil
import sys
import tempfile
from difflib import SequenceMatcher
from pathlib import Path

BANNED = re.compile(
    r"hope this (e-?mail|message) finds|keen interest|writing to express|\bdelv(e|es|ing)\b|passion|leverag"
    r"|cutting[- ]edge|groundbreaking|innovative|\balign(s|ed)?\b|resonat|particularly struck|furthermore"
    r"|moreover|rapidly evolving|unique opportunity|great fit|contribute meaningfully|intersection of"
    r"|fascinat|invaluable|honou?red|esteemed|renowned|outstanding|impressive|thrilled|game[- ]chang",
    re.I,
)
SENTENCE_LIMIT = 0.6  # word-level match ratio; unrelated sentences score about 0.1
SHAPE_LIMIT = 0.4     # stricter for opening and closing lines
SUBJECT_LIMIT = 0.7
STYLE_KEYS = ("opening_style", "part_order", "closing_style")


def parse(text):
    meta = dict(re.findall(r"^(\w+):[ \t]*(.*)$", text.split("## Body")[0], re.M))
    found = re.search(r"## Body\s*\n(.*?)\n## Sign-off", text, re.S)
    body = found.group(1).strip() if found else ""
    return meta, re.sub(r"^(Dear|Hi|Hello)\b[^\n]*\n+", "", body)  # salutation doesn't count


def sentences(body):
    # ponytail: naive split, "e.g." breaks a sentence in two; fine for spotting reused wording
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if len(s.split()) >= 4]


def words(text):
    return re.findall(r"[\w'-]+", text.lower())


def sim(a, b):
    return SequenceMatcher(None, words(a), words(b), autojunk=False).ratio()


def same_shape(a, b):
    return words(a)[:3] == words(b)[:3] or sim(a, b) >= SHAPE_LIMIT


def check(path):
    path = Path(path)
    meta, body = parse(path.read_text(encoding="utf-8"))
    problems = []

    count = len(body.split())
    if not 110 <= count <= 170:
        problems.append(f"body is {count} words, needs 110 to 170")
    paragraphs = [p for p in re.split(r"\n\s*\n", body) if p.strip()]
    if not 2 <= len(paragraphs) <= 4:
        problems.append(f"{len(paragraphs)} paragraphs, needs 2 to 4")
    full = meta.get("subject", "") + "\n" + body
    for hit in sorted({m.group(0).lower() for m in BANNED.finditer(full)}):
        problems.append(f"banned wording: {hit}")
    if re.search(r"[—–]| -- ", full):
        problems.append("em or en dash")
    if re.search(r"^\s*([-*•]|\d+[.)])\s", body, re.M):
        problems.append("list or bullet in body")
    if "**" in body or "__" in body:
        problems.append("bold text in body")
    if not re.search(r"\bCV\b|\br[eé]sum[eé]\b", body, re.I):
        problems.append("doesn't say the CV is attached")
    if not meta.get("subject"):
        problems.append("no subject")

    others = sorted((p for p in path.parent.glob("*.md") if p != path),
                    key=lambda p: p.stat().st_mtime, reverse=True)
    parsed = [(p.name, *parse(p.read_text(encoding="utf-8"))) for p in others]
    mine = sentences(body)

    closest = (0.0, "none", "", "")
    for name, other_meta, other_body in parsed:
        theirs = sentences(other_body)
        for a in mine:
            for b in theirs:
                score = sim(a, b)
                if score > closest[0]:
                    closest = (score, name, a, b)
        if mine and theirs:
            if same_shape(mine[0], theirs[0]):
                problems.append(f"opening has the same shape as {name}: {theirs[0]!r}")
            if same_shape(mine[-1], theirs[-1]):
                problems.append(f"closing has the same shape as {name}: {theirs[-1]!r}")
        if sim(meta.get("subject", ""), other_meta.get("subject", "")) >= SUBJECT_LIMIT:
            problems.append(f"subject too close to {name}: {other_meta.get('subject')!r}")
    if closest[0] >= SENTENCE_LIMIT:
        problems.append(f"sentence too close to {closest[1]} ({closest[0]:.2f}): {closest[2]!r}")

    for key in STYLE_KEYS:
        value = meta.get(key, "").strip().lower()
        if not value:
            problems.append(f"missing {key}")
        for name, other_meta, _ in parsed[:10]:
            if value and value == other_meta.get(key, "").strip().lower():
                problems.append(f"{key} '{value}' already used in {name} (last 10 drafts)")

    summary = f"words={count} paragraphs={len(paragraphs)} closest={closest[0]:.2f} vs {closest[1]}"
    return problems, summary


def selftest():
    sent = [f"alpha{i} beta{i} gamma{i} delta{i} epsilon{i} zeta{i} eta{i} theta{i} iota{i} kappa{i}." for i in range(12)]
    draft = ("subject: {s}\nopening_style: {k}\npart_order: {k}\nclosing_style: {k}\n\n## Body\n\nDear Prof X,\n\n"
             "{a}\n\n{b} {cv}\n\n## Sign-off\n\nNiloy\n")

    def make(subject, style, lines, cv="My CV is attached."):
        return draft.format(s=subject, k=style, a=" ".join(lines[:6]), b=" ".join(lines[6:]), cv=cv)

    tmp = Path(tempfile.mkdtemp())
    try:
        a = tmp / "a.md"
        a.write_text(make("Testing patches", "paper", sent), encoding="utf-8")
        assert check(a)[0] == [], check(a)[0]

        b = tmp / "b.md"
        b.write_text(make("Testing patches", "paper", sent), encoding="utf-8")  # copy of a
        text = " ".join(check(b)[0])
        for expected in ("same shape", "subject too close", "sentence too close", "already used"):
            assert expected in text, expected

        fresh = [s.replace("alpha", "one").replace("beta", "two").replace("gamma", "three").replace("delta", "four")
                 .replace("epsilon", "five").replace("zeta", "six").replace("eta", "seven").replace("theta", "eight")
                 .replace("iota", "nine").replace("kappa", "ten") for s in sent]
        other_cv = "You can see everything else on the CV I sent along."
        b.write_text(make("A different thing entirely", "problem", fresh, other_cv), encoding="utf-8")
        assert check(b)[0] == [], check(b)[0]

        b.write_text(make("A different thing entirely", "problem", fresh, "I delve — see my CV here today."), encoding="utf-8")
        text = " ".join(check(b)[0])
        assert "banned" in text and "dash" in text, text

        b.write_text(make("A different thing entirely", "problem", fresh[:3], other_cv), encoding="utf-8")
        assert "words" in " ".join(check(b)[0])
    finally:
        shutil.rmtree(tmp)
    print("selftest ok")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:] == ["--selftest"]:
        selftest()
    elif len(sys.argv) == 2:
        issues, info = check(sys.argv[1])
        print(info)
        for issue in issues:
            print("FAIL:", issue)
        print("FAIL" if issues else "PASS")
        sys.exit(1 if issues else 0)
    else:
        sys.exit(__doc__)
