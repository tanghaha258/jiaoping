from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"

TEXT_FILE_SUFFIXES = {".vue", ".ts", ".tsx", ".js", ".jsx", ".scss", ".css"}

MOJIBAKE_TOKENS = [
    "鐧",
    "鏁",
    "瀛",
    "璺",
    "绠",
    "璧",
    "鎻",
    "閽",
    "骞",
    "椹",
    "鑸",
    "妯",
    "浠",
    "妗",
    "闄",
    "鏈",
    "兘",
    "垪",
    "栧",
    "€",
]

BROKEN_FRAGMENTS = [
    "?/span>",
    "?/div>",
    "?/nav>",
    "aria-label=\"",
]

EXPECTED_TEXT = {
    "frontend/src/router/routes.ts": [
        "登录",
        "教师工作台",
        "AI教学方案",
        "学生学习",
        "教研工作台",
        "管理后台",
        "AI智能体",
        "404 页面未找到",
    ],
    "frontend/src/router/index.ts": ["智跨学评"],
    "frontend/src/layouts/AppLayout.vue": [
        "跨学科教学评一体化",
        "AI智能体平台",
        "教学设计",
        "智能备课",
        "智能评价",
    ],
    "frontend/src/layouts/RoleMenu.vue": [
        "教学核心应用",
        "AI生成教学方案",
        "跨学科任务设计",
        "学情诊断与分析",
        "平台治理",
        "审计日志",
    ],
}


def iter_source_files() -> list[Path]:
    return sorted(
        path
        for path in FRONTEND_SRC.rglob("*")
        if path.is_file() and path.suffix in TEXT_FILE_SUFFIXES
    )


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def collect_text_errors() -> list[str]:
    errors: list[str] = []

    for path in iter_source_files():
        relative = rel(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{relative}: not valid UTF-8 ({exc})")
            continue

        if "\ufffd" in text:
            errors.append(f"{relative}: contains Unicode replacement character U+FFFD")

        for token in MOJIBAKE_TOKENS:
            if token in text:
                errors.append(f"{relative}: contains likely mojibake token {token!r}")

        for fragment in BROKEN_FRAGMENTS[:3]:
            if fragment in text:
                errors.append(f"{relative}: contains broken template fragment {fragment!r}")

        if "aria-label=\"" in text:
            for line_number, line in enumerate(text.splitlines(), start=1):
                if "aria-label=\"" in line and line.count('"') % 2 != 0:
                    errors.append(f"{relative}:{line_number}: contains unterminated aria-label")

    for relative, labels in EXPECTED_TEXT.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"{relative}: expected source file is missing")
            continue

        text = path.read_text(encoding="utf-8")
        for label in labels:
            if label not in text:
                errors.append(f"{relative}: missing expected label {label!r}")

    return errors


def main() -> int:
    if not FRONTEND_SRC.exists():
        print(f"Frontend source directory not found: {FRONTEND_SRC}", file=sys.stderr)
        return 1

    errors = collect_text_errors()
    if errors:
        print("Frontend text health check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Frontend text health check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
