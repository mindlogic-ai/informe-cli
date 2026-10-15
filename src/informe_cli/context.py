"""How full a session's context window is.

Nothing here measures anything. The server already tracks this number on every
turn of every surface — it is the same count `COMPACTION_THRESHOLD_TOKENS` is
judged against — and hands it to clients as three fields:
`context_tokens`, `context_window`, `context_compact_at`. They ride on the run
snapshot that ends a turn, on `GET /v1/sessions/{key}/history`, and on the
session listing. The CLI simply had no code that looked at them.

A second estimate computed here would eventually disagree with the one that
actually fires compaction, which is the whole reason to reshape rather than
recompute.
"""
from __future__ import annotations


def block(payload: dict | None) -> dict | None:
    """Server fields → the CLI's `context` object. None when the server omitted them.

    Absent is not zero: an older server, or a session this process has never
    held in memory, reports nothing rather than an empty window, and a caller
    deciding "should I compact" must be able to tell those apart.
    """
    if not payload:
        return None
    tokens = payload.get("context_tokens")
    if tokens is None:
        return None
    window = int(payload.get("context_window") or 0) or None
    compact_at = int(payload.get("context_compact_at") or 0) or None
    tokens = int(tokens)
    return {
        "input_tokens": tokens,
        "limit_tokens": window,
        "compact_at_tokens": compact_at,
        # Against the compaction threshold, not the window. The question this
        # number is read to answer is "how long until this compacts", and the
        # window is not where that happens — 700K of 1M is 70% of the window
        # and 100% of the thing about to fire, so pacing to the window means
        # being surprised by a compaction at "70% full".
        "fraction": round(tokens / compact_at, 4) if compact_at else None,
        # The window still gets a number, as its own field: it is what a caller
        # sizing one large prompt cares about, which is a different question
        # from when the transcript gets summarized.
        "fraction_of_window": round(tokens / window, 4) if window else None,
    }


def short(n: int | None) -> str:
    """`142000` → `142K`. Shared with the compact command's before/after line."""
    if n is None:
        return "?"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def line(ctx: dict | None) -> str | None:
    """One human line: `context: 142K / 700K before auto-compact (20%) · window 1M`.

    The headline pair is the threshold, for the same reason `fraction` is: the
    compaction is the event a reader is pacing to. The window trails it as
    context rather than leading, so the two percentages can never be confused
    for each other.
    """
    if not ctx:
        return None
    if ctx.get("compact_at_tokens"):
        out = (
            f"context: {short(ctx['input_tokens'])} / "
            f"{short(ctx['compact_at_tokens'])} before auto-compact"
        )
    else:
        out = f"context: {short(ctx['input_tokens'])}"
    if ctx.get("fraction") is not None:
        out += f" ({ctx['fraction'] * 100:.0f}%)"
    if ctx.get("limit_tokens"):
        out += f" · window {short(ctx['limit_tokens'])}"
    return out


def brief(ctx: dict | None) -> str:
    """Column-sized form for list rows: `142K ctx` (empty when unknown)."""
    if not ctx or not ctx["input_tokens"]:
        return ""
    return f"{short(ctx['input_tokens'])} ctx"
