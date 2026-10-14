"""Shared helpers for TTS providers."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

CODE_READ_MAP = [
    (re.compile(r"\bnpm install\b", re.I), "N-P-M install"),
    (re.compile(r"\bgit clone\b", re.I), "git clone"),
    (re.compile(r"\bAPI\b"), "A-P-I"),
    (re.compile(r"\bJSON\b"), "Jason"),
    (re.compile(r"\bURL\b"), "U-R-L"),
    (re.compile(r"O\(n\)", re.I), "O of n"),
]

_SENTENCE_SPLIT = re.compile(
    r"(?<=[。！？!?；;…])\s*|(?<=[.!?])(?=\s+[A-Z「『\"'(\u4e00-\u9fff])"
)


def detect_lang(text: str) -> str:
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return "zh" if cjk >= max(1, len(text) // 8) else "en"


def preprocess_script(text: str) -> str:
    t = text.strip()
    t = re.sub(r"[`*_#>]+", "", t)
    t = re.sub(r"\([^)]*(说|语气|平静|缓慢)[^)]*\)", "", t)
    t = re.sub(r"（[^）]*(说|语气|平静|缓慢)[^）]*）", "", t)
    for pat, repl in CODE_READ_MAP:
        t = pat.sub(repl, t)

    def path_repl(m: re.Match) -> str:
        p = m.group(0)
        p = p.replace("/", " slash ").replace(".", " dot ")
        p = re.sub(r"\bts\b", "T-S", p, flags=re.I)
        p = re.sub(r"\bjs\b", "J-S", p, flags=re.I)
        return p

    t = re.sub(r"\b[\w.-]+/[\w./-]+\b", path_repl, t)
    return re.sub(r"\s+", " ", t).strip()


def split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n|^## .+$", text, flags=re.M)
    segs = [preprocess_script(p) for p in parts if preprocess_script(p)]
    return segs or [preprocess_script(text)]


def chunk_by_sentences(text: str, max_chars: int) -> list[str]:
    """Split text into chunks ≤ max_chars at sentence boundaries when possible."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Prefer paragraph / blank-line pieces first
    pieces: list[str] = []
    for para in re.split(r"\n+", text):
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_chars:
            pieces.append(para)
            continue
        # Sentence split
        sentences = [s.strip() for s in _SENTENCE_SPLIT.split(para) if s and s.strip()]
        if not sentences:
            sentences = [para]
        buf = ""
        for s in sentences:
            if len(s) > max_chars:
                if buf:
                    pieces.append(buf)
                    buf = ""
                # Hard wrap oversized sentence
                for i in range(0, len(s), max_chars):
                    pieces.append(s[i : i + max_chars])
                continue
            candidate = f"{buf}{s}" if not buf else f"{buf}{s}"
            # Prefer space between EN sentences
            if buf and not buf.endswith((" ", "\n")) and not s.startswith((" ",)):
                # Chinese often has no space; English might need one
                if buf[-1].isascii() and s[0].isascii():
                    candidate = f"{buf} {s}"
                else:
                    candidate = f"{buf}{s}"
            if len(candidate) <= max_chars:
                buf = candidate
            else:
                if buf:
                    pieces.append(buf)
                buf = s
        if buf:
            pieces.append(buf)

    # Merge tiny leftovers into previous when possible
    merged: list[str] = []
    for p in pieces:
        if merged and len(merged[-1]) + 1 + len(p) <= max_chars:
            sep = " " if merged[-1][-1].isascii() and p[0].isascii() else ""
            merged[-1] = f"{merged[-1]}{sep}{p}"
        else:
            merged.append(p)
    return merged or [text[:max_chars]]


def ffmpeg_concat(paths: list[Path], out_path: Path) -> None:
    if not paths:
        raise ValueError("没有可拼接的音频")
    if len(paths) == 1:
        shutil.copy2(paths[0], out_path)
        return
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("需要 ffmpeg 才能 --concat")
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
        list_path = Path(f.name)
        for p in paths:
            esc = str(p.resolve()).replace("'", r"'\''")
            f.write(f"file '{esc}'\n")
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c",
            "copy",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            codec = "libmp3lame" if out_path.suffix.lower() == ".mp3" else "pcm_s16le"
            cmd2 = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c:a",
                codec,
                str(out_path),
            ]
            proc2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
            if proc2.returncode != 0:
                raise RuntimeError(
                    f"ffmpeg concat 失败:\n{proc.stderr[-500:]}\n---\n{proc2.stderr[-500:]}"
                )
    finally:
        list_path.unlink(missing_ok=True)


def convert_audio(src: Path, dest: Path) -> None:
    """Convert audio to dest format via ffmpeg when suffixes differ."""
    if src.suffix.lower() == dest.suffix.lower():
        if src.resolve() != dest.resolve():
            shutil.copy2(src, dest)
        return
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(f"需要 ffmpeg 才能把 {src.suffix} 转为 {dest.suffix}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    codec = "libmp3lame" if dest.suffix.lower() == ".mp3" else "pcm_s16le"
    proc = subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), "-c:a", codec, str(dest)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 转码失败: {proc.stderr[-400:]}")


def load_style_prompt(name: str, lang: str, prompts_dir: Path | None = None) -> str:
    """Load prompts/<name>-{zh|en}.txt; fall back to sibling en/zh."""
    root = prompts_dir
    if root is None:
        # scripts/providers/common.py → repo/prompts
        root = Path(__file__).resolve().parents[2] / "prompts"
        if not root.is_dir():
            # Claude skill layout: <skill>/prompts next to scripts/
            root = Path(__file__).resolve().parents[1].parent / "prompts"
    path = root / f"{name}-{lang}.txt"
    if not path.is_file():
        alt = "en" if lang == "zh" else "zh"
        path = root / f"{name}-{alt}.txt"
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""
