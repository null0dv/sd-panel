#!/usr/bin/env python3
"""Extract PROMPTs from Grok export conversations:
P / P 格式 / D / D 格式
→ Markdown archive + JSON DB + char-banks + templates import package.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SRC = Path(
    r"C:\Users\User\Desktop\ttl\30d\export_data"
    r"\66328770-51f5-446b-811b-a94238f3e6bf\prod-grok-backend.json"
)
OUT_DIR = Path(__file__).resolve().parent.parent / "data"
BANKS_PATH = OUT_DIR / "char-banks.json"
DB_PATH = OUT_DIR / "p-prompt-db.json"
MD_PATH = OUT_DIR / "p-prompt-archive.md"
TEMPLATES_PATH = OUT_DIR / "p-prompt-templates.json"
IMPORT_PKG_PATH = OUT_DIR / "p-import-char-banks.json"

SECTION_MAP = OrderedDict(
    [
        ("Subject & Character", "subject"),
        ("Facial Features", "face"),
        ("Character Details", "details"),
        ("Outfit", "outfit"),
        ("Pose / Composition", "pose"),
        ("Pose / Composition & Act", "pose"),
        ("JOB / Act", "job"),
        ("Environment & Lighting", "env"),
        ("STYLE REFERENCES", "styleRef"),
        ("QUALITY / TECHNICAL TAGS", "quality"),
    ]
)

HEADER_RE = re.compile(r"//\s*❖\s*([^\n]+)", re.I)
PFORMAT_START = re.compile(r"//\s*❖\s*Subject", re.I)
CODE_FENCE = re.compile(r"```(?:prompt|text)?\s*\n(.*?)```", re.S | re.I)

# Assistant wrappers that introduce a clean D-format flat prompt
CLEAN_LEAD_RE = re.compile(
    r"(?:"
    r"\*\*已移除格式的干净提示词[：:]*\*\*"
    r"|\*\*已移除格式的乾淨提示詞[：:]*\*\*"
    r"|\*\*D格式輸出[^*]{0,80}\*\*"
    r"|D格式輸出[（(][^）)]{0,40}[）)][：:]?"
    r"|已移除所有段落[^\n]{0,40}[：:]?"
    r"|只保留[^\n]{0,20}提示詞[：:]?"
    r")\s*",
    re.I,
)

SECTION_ORDER = [
    "subject",
    "face",
    "details",
    "outfit",
    "pose",
    "job",
    "env",
    "styleRef",
    "quality",
]
SECTION_LABELS = {
    "subject": "Subject & Character",
    "face": "Facial Features",
    "details": "Character Details",
    "outfit": "Outfit",
    "pose": "Pose / Composition",
    "job": "JOB / Act",
    "env": "Environment & Lighting",
    "styleRef": "STYLE REFERENCES",
    "quality": "QUALITY / TECHNICAL TAGS",
}


def content_hash(text: str) -> str:
    t = re.sub(r"\s+", " ", text.lower()).strip()
    return hashlib.sha1(t.encode("utf-8")).hexdigest()[:12]


def strip_wrapper(msg: str) -> str:
    msg = msg.strip()
    fences = CODE_FENCE.findall(msg)
    if not fences:
        return msg
    fences_sorted = sorted(fences, key=len, reverse=True)
    for f in fences_sorted:
        if PFORMAT_START.search(f) or "// ❖" in f:
            return f.strip()
    return fences_sorted[0].strip()


def extract_pformat_blocks(text: str) -> list[str]:
    text = strip_wrapper(text)
    if not text:
        return []
    blocks: list[str] = []
    starts = [m.start() for m in PFORMAT_START.finditer(text)]
    if not starts:
        if HEADER_RE.search(text) and text.count("// ❖") >= 3:
            blocks.append(text.strip())
        return blocks

    cut_markers = [
        "\n\n---",
        "\n\n**",
        "\n\n需要",
        "\n\n如果你",
        "\n\n以上是",
        "\n\n✅",
        "\n\n已",
        "\n\n說明",
        "\n\n备注",
        "\n\nNote:",
        "\n\n我已",
        "\n\n這份",
        "\n\n这个",
        "\n\n這個",
        "\n\n下面",
        "\n\n以下是",
    ]

    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(text)
        block = text[s:e].strip()
        last_h = None
        for m in HEADER_RE.finditer(block):
            last_h = m
        if last_h:
            tail = block[last_h.end() :]
            for mk in cut_markers:
                idx = tail.find(mk)
                if idx != -1 and idx > 20:
                    block = block[: last_h.end() + idx].strip()
                    break
        if len(block) > 80 and block.count("// ❖") >= 3:
            blocks.append(block)
    return blocks


def resolve_section_key(header: str) -> str | None:
    h_clean = header.strip()
    for name, k in SECTION_MAP.items():
        if name.lower() in h_clean.lower() or h_clean.lower() in name.lower():
            return k
    hl = h_clean.lower()
    if "subject" in hl or ("character" in hl and "detail" not in hl):
        return "subject"
    if "facial" in hl or "face" in hl:
        return "face"
    if "detail" in hl:
        return "details"
    if "outfit" in hl or "costume" in hl:
        return "outfit"
    if "pose" in hl or "composition" in hl:
        return "pose"
    if "job" in hl or re.search(r"\bact\b", hl):
        return "job"
    if "environment" in hl or "lighting" in hl:
        return "env"
    if "style" in hl:
        return "styleRef"
    if "quality" in hl or "technical" in hl:
        return "quality"
    return None


def parse_sections(block: str) -> dict[str, str]:
    parts = re.split(r"(?://\s*❖\s*[^\n]+)", block)
    headers = HEADER_RE.findall(block)
    result: dict[str, str] = {}
    for h, body in zip(headers, parts[1:]):
        key = resolve_section_key(h)
        if not key:
            continue
        body = body.strip()
        body = re.sub(r"^[\s,，]+", "", body)
        body = re.sub(r"[\s,，]+$", "", body)
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\n+", " ", body)
        body = re.sub(r"\s*,\s*", ", ", body)
        body = re.sub(r"(,\s*){2,}", ", ", body).strip(" ,")
        if len(body) < 3:
            continue
        if key not in result or len(body) > len(result[key]):
            result[key] = body
    return result


def normalize_prompt_text(sections: dict[str, str]) -> str:
    lines: list[str] = []
    for k in SECTION_ORDER:
        if sections.get(k):
            lines.append(f"// ❖ {SECTION_LABELS[k]}")
            lines.append(sections[k])
            lines.append("")
    return "\n".join(lines).strip()


def get_time(r: dict) -> str:
    ct = r.get("create_time")
    if isinstance(ct, dict):
        return ct.get("$date") or ""
    return str(ct or "")


def is_target_title(title: str) -> bool:
    t = (title or "").strip()
    if t in ("P", "D"):
        return True
    if t.startswith("P 格式") or t.startswith("P格式"):
        return True
    if t.startswith("D 格式") or t.startswith("D格式"):
        return True
    if t in (
        "P對話窗",
        "P格式對話窗",
        "P 對話窗",
        "P 格式對話窗",
        "D對話窗",
        "D格式對話窗",
        "D 對話窗",
        "D 格式對話窗",
    ):
        return True
    return False


def chinese_ratio(text: str) -> float:
    if not text:
        return 0.0
    cn = len(re.findall(r"[\u4e00-\u9fff]", text))
    return cn / max(len(text), 1)


def clean_flat_prompt(text: str) -> str:
    t = text.strip()
    t = re.sub(r"^[\s*#>-]+", "", t)
    # drop trailing assistant follow-ups
    for mk in (
        "\n\n---",
        "\n\n**",
        "\n\n需要",
        "\n\n如果你",
        "\n\n以上",
        "\n\n說明",
        "\n\n备注",
        "\n\n是否",
        "\n\n還要",
        "\n\n还要",
        "\n\n我可以",
        "\n\n想再",
    ):
        idx = t.find(mk)
        if idx > 80:
            t = t[:idx]
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n+", " ", t)
    t = re.sub(r"\s*,\s*", ", ", t)
    t = re.sub(r"(,\s*){2,}", ", ", t).strip(" ,\n\r\t")
    return t


def looks_like_flat_prompt(text: str) -> bool:
    t = clean_flat_prompt(text)
    if len(t) < 80 or len(t) > 4000:
        return False
    if t.count(",") < 10:
        return False
    if chinese_ratio(t) > 0.18:
        return False
    # reject pure instruction
    if re.match(r"^(請|帮|幫|把|将|將|写|寫|D格式|P格式)", t):
        return False
    return True


def extract_flat_prompts(msg: str) -> list[str]:
    """Extract D-format flat prompts from assistant/human messages."""
    out: list[str] = []
    raw = msg.strip()
    if not raw:
        return out

    # fenced blocks first
    for f in CODE_FENCE.findall(raw):
        if looks_like_flat_prompt(f) and "// ❖" not in f:
            out.append(clean_flat_prompt(f))

    # after clean-lead markers
    for m in CLEAN_LEAD_RE.finditer(raw):
        tail = raw[m.end() :]
        # take until markdown section / chinese prose block
        cut = len(tail)
        for mk in ("\n\n**", "\n\n---", "\n\n需要", "\n\n如果", "\n\n以上", "\n\n是否"):
            i = tail.find(mk)
            if i != -1 and i < cut:
                cut = i
        chunk = tail[:cut]
        if looks_like_flat_prompt(chunk):
            out.append(clean_flat_prompt(chunk))

    # whole message as flat (common in D conversation)
    if not out and looks_like_flat_prompt(raw) and "// ❖" not in raw:
        # strip leading D-format instruction line
        body = raw
        if re.match(r"^D格式", body):
            parts = re.split(r"\n\s*\n", body, maxsplit=1)
            if len(parts) == 2 and looks_like_flat_prompt(parts[1]):
                body = parts[1]
            else:
                return out
        out.append(clean_flat_prompt(body))

    # dedupe within message
    seen_local: set[str] = set()
    uniq: list[str] = []
    for p in out:
        h = content_hash(p)
        if h in seen_local:
            continue
        seen_local.add(h)
        uniq.append(p)
    return uniq


def empty_template_from_flat(flat: str) -> dict[str, str]:
    """Store full D flat prompt in subject so template mode can still surface it."""
    return {
        "subject": flat,
        "face": "",
        "details": "",
        "outfit": "",
        "pose": "",
        "job": "",
        "env": "",
        "styleRef": "",
        "quality": "",
    }


def main() -> None:
    print("Loading export...", flush=True)
    with open(SRC, "r", encoding="utf-8") as f:
        data = json.load(f)

    targets = []
    for i, c in enumerate(data["conversations"]):
        title = (c["conversation"].get("title") or "").strip()
        if is_target_title(title):
            targets.append((i, title, c))

    # stable order: P, P 格式, D, D 格式
    order = {"P": 0, "P 格式": 1, "P格式": 1, "D": 2, "D 格式": 3, "D格式": 3}
    targets.sort(key=lambda x: order.get(x[1].strip(), 9))

    print(
        "Targets:",
        [(i, repr(t), len(c["responses"])) for i, t, c in targets],
        flush=True,
    )
    if not targets:
        raise SystemExit("No P/D conversations found")

    records: list[dict] = []
    seen: set[str] = set()
    bank_adds: dict[str, list[str]] = defaultdict(list)
    bank_seen: dict[str, set[str]] = defaultdict(set)

    def add_record(
        *,
        title: str,
        conv_id: str | None,
        j: int,
        sender: str,
        time: str,
        kind: str,
        sections: dict,
        full: str,
    ) -> None:
        h = content_hash(full)
        if h in seen:
            return
        seen.add(h)
        rec = {
            "id": f"p-{len(records) + 1:04d}",
            "source_title": title.strip(),
            "conversation_id": conv_id,
            "response_index": j,
            "sender": sender,
            "time": time,
            "kind": kind,
            "sections": sections,
            "full_prompt": full,
            "hash": h,
        }
        records.append(rec)
        for k, v in sections.items():
            vv = v.strip()
            if len(vv) < 8 or len(vv) > 1200:
                continue
            vk = content_hash(vv)
            if vk not in bank_seen[k]:
                bank_seen[k].add(vk)
                bank_adds[k].append(vv)

    for _idx, title, conv_wrap in targets:
        conv = conv_wrap["conversation"]
        resps = conv_wrap["responses"]
        is_d = title.strip().upper().startswith("D")
        for j, item in enumerate(resps):
            r = item["response"]
            msg = r.get("message") or ""
            sender = r.get("sender") or ""
            if not msg or len(msg) < 40:
                continue

            blocks = extract_pformat_blocks(msg)
            if not blocks and (PFORMAT_START.search(msg) or msg.count("// ❖") >= 4):
                blocks = extract_pformat_blocks(msg)

            for block in blocks:
                sections = parse_sections(block)
                if len(sections) < 3 and "subject" not in sections:
                    continue
                full = normalize_prompt_text(sections) if sections else block
                if not full:
                    full = block
                add_record(
                    title=title,
                    conv_id=conv.get("id"),
                    j=j,
                    sender=sender,
                    time=get_time(r),
                    kind="p_format" if sections else "p_format_raw",
                    sections=sections,
                    full=full,
                )

            # D / D格式 flat prompts (and dense tag dumps in P)
            flats = extract_flat_prompts(msg)
            if not flats and sender == "human" and not blocks:
                if (
                    len(msg) > 500
                    and msg.count(",") >= 15
                    and chinese_ratio(msg[:300]) < 0.15
                    and "// ❖" not in msg
                ):
                    flats = [clean_flat_prompt(msg)]

            for flat in flats:
                # skip if same as already stored p-format normalized
                kind = "d_format_flat" if is_d else "raw_tag_prompt"
                add_record(
                    title=title,
                    conv_id=conv.get("id"),
                    j=j,
                    sender=sender,
                    time=get_time(r),
                    kind=kind,
                    sections={},
                    full=flat,
                )

    print(f"Extracted records: {len(records)}", flush=True)
    print("Bank adds:", {k: len(v) for k, v in bank_adds.items()}, flush=True)
    by_src = defaultdict(int)
    by_kind = defaultdict(int)
    for rec in records:
        by_src[rec["source_title"]] += 1
        by_kind[rec["kind"]] += 1
    print("By source:", dict(by_src), flush=True)
    print("By kind:", dict(by_kind), flush=True)

    banks = json.loads(BANKS_PATH.read_text(encoding="utf-8"))
    merged_counts: dict[str, int] = {}
    for k, vals in bank_adds.items():
        if k not in banks:
            banks[k] = []
        before = len(banks[k])
        existing = set(banks[k])
        for v in vals:
            if v not in existing:
                banks[k].append(v)
                existing.add(v)
        merged_counts[k] = len(banks[k]) - before

    BANKS_PATH.write_text(
        json.dumps(banks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Merged into char-banks:", merged_counts, flush=True)

    templates: list[dict] = []
    tpl_seen: set[str] = set()
    for rec in records:
        sec = rec.get("sections") or {}
        if sec.get("subject"):
            key = (sec.get("subject", ""), sec.get("outfit", ""), sec.get("pose", ""))
            kh = content_hash("|".join(key))
            if kh in tpl_seen:
                continue
            tpl_seen.add(kh)
            templates.append(
                {
                    "id": rec["id"],
                    "source": rec["source_title"],
                    "subject": sec.get("subject", ""),
                    "face": sec.get("face", ""),
                    "details": sec.get("details", ""),
                    "outfit": sec.get("outfit", ""),
                    "pose": sec.get("pose", ""),
                    "job": sec.get("job", ""),
                    "env": sec.get("env", ""),
                    "styleRef": sec.get("styleRef", ""),
                    "quality": sec.get("quality", ""),
                }
            )
        elif rec["kind"] in ("d_format_flat", "raw_tag_prompt"):
            flat = rec["full_prompt"]
            if len(flat) < 80 or len(flat) > 2000:
                continue
            kh = content_hash("flat|" + flat)
            if kh in tpl_seen:
                continue
            tpl_seen.add(kh)
            t = empty_template_from_flat(flat)
            t["id"] = rec["id"]
            t["source"] = rec["source_title"]
            templates.append(t)

    db = {
        "version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(SRC),
        "conversations": [
            {
                "title": t.strip(),
                "id": c["conversation"].get("id"),
                "create_time": c["conversation"].get("create_time"),
                "modify_time": c["conversation"].get("modify_time"),
                "response_count": len(c["responses"]),
                "starred": c["conversation"].get("starred"),
            }
            for _, t, c in targets
        ],
        "stats": {
            "prompt_records": len(records),
            "templates": len(templates),
            "by_source": dict(by_src),
            "by_kind": dict(by_kind),
            "bank_added": merged_counts,
            "bank_total_after": {k: len(banks[k]) for k in banks},
        },
        "templates": templates,
        "prompts": records,
    }
    DB_PATH.write_text(
        json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print("Wrote", DB_PATH, "size", DB_PATH.stat().st_size, flush=True)

    # engine templates (no id/source required)
    tpls_slim = [
        {
            k: t.get(k, "")
            for k in [
                "subject",
                "face",
                "details",
                "outfit",
                "pose",
                "job",
                "env",
                "styleRef",
                "quality",
            ]
        }
        for t in templates
    ]
    TEMPLATES_PATH.write_text(
        json.dumps(tpls_slim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    pkg = {
        "banks": banks,
        "templates": tpls_slim,
        "meta": {
            "source": "ttl P/P格式/D/D格式",
            "version": 2,
            "template_count": len(tpls_slim),
            "prompt_records": len(records),
        },
    }
    IMPORT_PKG_PATH.write_text(
        json.dumps(pkg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "Wrote templates",
        len(tpls_slim),
        "import pkg",
        IMPORT_PKG_PATH.stat().st_size,
        flush=True,
    )

    md: list[str] = []
    md.append("# P / D 對話窗 PROMPT 完整節錄")
    md.append("")
    md.append(
        f"> 來源：桌面 `ttl` Grok 匯出 · 產生時間 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    md.append(">")
    md.append("> 涵蓋對話：")
    for _, t, c in targets:
        md.append(
            f"> - **{t.strip()}**（{len(c['responses'])} 則訊息，"
            f"id `{c['conversation'].get('id')}`）"
        )
    md.append("")
    md.append("## 統計")
    md.append("")
    md.append("| 項目 | 數量 |")
    md.append("|------|------|")
    md.append(f"| 去重後完整 PROMPT | {len(records)} |")
    md.append(f"| 可匯入樣板 templates | {len(templates)} |")
    for src, n in by_src.items():
        md.append(f"| 來自 {src} | {n} |")
    for kind, n in by_kind.items():
        md.append(f"| kind={kind} | {n} |")
    for k, n in merged_counts.items():
        md.append(f"| 本批新增 char-banks.{k} | {n} |")
    md.append("")
    md.append("## 匯入 VOID.RNG")
    md.append("")
    md.append("本節錄已同步處理為：")
    md.append("")
    md.append(
        "- `void-rng/data/p-prompt-db.json` — 完整 PROMPT 資料庫（records + templates）"
    )
    md.append(
        "- `void-rng/data/char-banks.json` — 分段標籤已合併進角色辭庫（RNG 亂數會直接用到）"
    )
    md.append(
        "- `void-rng/data/p-prompt-templates.json` — 完整樣板（template 模式，含 D 扁平 prompt）"
    )
    md.append(
        "- `void-rng/data/p-import-char-banks.json` — 一鍵「匯入辭庫」用封包（手動備援）"
    )
    md.append("")
    md.append("重新啟動 **VOID.RNG** 後，角色頁的 bank / template 即包含本批資料。")
    md.append(
        "若本機 localStorage 有舊辭庫：角色頁 → **匯入辭庫** → 選 `p-import-char-banks.json`。"
    )
    md.append("")
    md.append("---")
    md.append("")

    for rec in records:
        md.append(
            f"## {rec['id']} · {rec['source_title']} · #{rec['response_index']}"
        )
        md.append("")
        md.append(f"- **sender**: `{rec['sender']}`")
        if rec.get("time"):
            md.append(f"- **time**: `{rec['time']}`")
        md.append(f"- **kind**: `{rec['kind']}`")
        md.append(f"- **hash**: `{rec['hash']}`")
        md.append("")
        if rec.get("sections"):
            md.append("### 分段")
            md.append("")
            for k in SECTION_ORDER:
                if rec["sections"].get(k):
                    md.append(f"**{k}**")
                    md.append("")
                    md.append(f"> {rec['sections'][k]}")
                    md.append("")
        md.append("### Full Prompt")
        md.append("")
        md.append("```prompt")
        md.append(rec["full_prompt"])
        md.append("```")
        md.append("")
        md.append("---")
        md.append("")

    MD_PATH.write_text("\n".join(md), encoding="utf-8")
    print("Wrote", MD_PATH, "size", MD_PATH.stat().st_size, "lines", len(md), flush=True)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
