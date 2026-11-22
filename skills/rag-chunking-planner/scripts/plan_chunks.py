#!/usr/bin/env python3
"""Chunk a folder of Markdown or text files and measure the result.

Usage (Python 3.9+, standard library only, no network):

    python plan_chunks.py plan <file-or-folder> --strategy fixed|heading|paragraph
        [--size 400] [--overlap 40] [--min-tokens 40] [--split-level 3]
        [--prefix-heading] [--questions questions.json] [--k 1,3,5]
        [--out chunks.jsonl] [--force]
    python plan_chunks.py compare <file-or-folder> --questions questions.json
        --setting paragraph:300:40 --setting heading:400:0 [--k 1,3,5]

What is read: .md, .markdown and .txt files under the path (recursive), and the
questions file. What is written: only the file given to --out, and only when
--out is used (an existing file is refused unless --force). Everything else is
printed to stdout as one strict JSON document.

Exit codes: 0 no error-level defect; 1 at least one error-level defect
(empty chunk, split code fence, split table, overlap above half the chunk size);
2 bad usage, unreadable input or malformed questions file (message on stderr).

Token unit: one token is one run of word characters or one punctuation mark.
This is a stable stand-in for model tokens (usually within roughly 25 percent
for English prose); it is not a real tokenizer.
"""
import argparse
import bisect
import hashlib
import json
import math
import os
import re
import statistics
import sys

TOKEN_RE = re.compile(r"\w+|[^\w\s]", re.UNICODE)
WORD_RE = re.compile(r"\w+", re.UNICODE)
HEADING_RE = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t#]*$")
FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
TABLE_RE = re.compile(r"^[ \t]*\|")
SENT_RE = re.compile(r"(?<=[.!?])\s+")
EXTENSIONS = (".md", ".markdown", ".txt")

STRATEGIES = ("fixed", "heading", "paragraph")
# A chunk above 1.5x the target size is reported as oversize: one whole
# paragraph, table or code block that cannot be cut without damaging it.
OVERSIZE_FACTOR = 1.5
# Overlap above half the chunk makes most of every chunk a repeat of the last.
MAX_OVERLAP_RATIO = 0.5
DEFAULT_MIN_TOKENS = 40  # below this a chunk rarely holds a complete answer
MAX_FILE_BYTES = 2_000_000  # larger files are skipped and listed, not read
MAX_FILES = 5000
EXAMPLES_PER_DEFECT = 5
MIN_PASSAGE_CHARS = 8  # shorter expected passages match almost anywhere
BM25_K1 = 1.5  # standard BM25 values; used only to compare settings
BM25_B = 0.75
HISTOGRAM_EDGES = (40, 100, 200, 400, 800)

ERROR_DEFECTS = ("empty_chunk", "split_code_fence", "split_table", "overlap_too_large")


class UsageError(Exception):
    pass


def ntok(text):
    return len(TOKEN_RE.findall(text))


def norm(text):
    return " ".join(text.lower().split())


# ---------------------------------------------------------------- scanning

def scan_text(text):
    """Return lines [(start, end, kind, level)], headings, fence spans, table spans.

    start is the first non-space offset of the line. kind is one of blank,
    heading, table, text, fence_open, fence (fence marker or fence body).
    """
    lines = []
    headings = []
    fence_spans = []
    fence = None
    fence_start = 0
    pos = 0
    for raw in text.split("\n"):
        end = pos + len(raw)
        indent = len(raw) - len(raw.lstrip())
        start = pos + indent
        level = None
        if fence is not None:
            kind = "fence"
            m = FENCE_RE.match(raw)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= fence[1] and raw.strip().strip(fence[0]) == "":
                fence_spans.append((fence_start, end))
                fence = None
        else:
            m = FENCE_RE.match(raw)
            if m:
                kind = "fence_open"
                fence = (m.group(1)[0], len(m.group(1)))
                fence_start = start
            elif not raw.strip():
                kind = "blank"
            else:
                hm = HEADING_RE.match(raw)
                if hm:
                    kind = "heading"
                    level = len(hm.group(1))
                    headings.append((start, level, hm.group(2).strip()))
                elif TABLE_RE.match(raw):
                    kind = "table"
                else:
                    kind = "text"
        lines.append((start, end, kind, level))
        pos = end + 1
    if fence is not None:
        fence_spans.append((fence_start, len(text)))
    table_spans = []
    run = None
    for (s, e, k, _l) in lines:
        if k == "table":
            run = (run[0], e) if run else (s, e)
        elif run:
            table_spans.append(run)
            run = None
    if run:
        table_spans.append(run)
    return lines, headings, fence_spans, table_spans


def heading_paths(headings):
    """Return (offsets, paths): the heading path in force from each heading on."""
    offsets, paths, stack = [], [], []
    for (off, level, title) in headings:
        stack = [x for x in stack if x[0] < level]
        stack.append((level, title))
        offsets.append(off)
        paths.append([t for (_lv, t) in stack])
    return offsets, paths


def path_at(offsets, paths, offset):
    i = bisect.bisect_right(offsets, offset) - 1
    return paths[i] if i >= 0 else []


# ---------------------------------------------------------------- strategies

def build_blocks(lines):
    """Group lines into blocks. A heading sticks to the block after it."""
    raw, cur = [], None
    for (s, e, k, _lv) in lines:
        if k == "blank":
            if cur:
                raw.append(cur)
                cur = None
            continue
        if k == "heading":
            if cur:
                raw.append(cur)
                cur = None
            raw.append({"start": s, "end": e, "kind": "heading"})
            continue
        if k == "fence_open":
            if cur:
                raw.append(cur)
            cur = {"start": s, "end": e, "kind": "fence"}
            continue
        kind = {"fence": "fence", "table": "table", "text": "para"}[k]
        if cur and cur["kind"] == kind:
            cur["end"] = e
        else:
            if cur:
                raw.append(cur)
            cur = {"start": s, "end": e, "kind": kind}
    if cur:
        raw.append(cur)
    out, pending = [], None
    for b in raw:
        if b["kind"] == "heading":
            if pending is None:
                pending = b["start"]
            continue
        if pending is not None:
            b["start"] = pending
            pending = None
        out.append(b)
    if pending is not None:
        out.append({"start": pending, "end": raw[-1]["end"], "kind": "heading"})
    return out


def expand_blocks(text, blocks, size):
    """Count tokens; cut paragraphs larger than size into sentences."""
    out = []
    for b in blocks:
        b["tokens"] = ntok(text[b["start"]:b["end"]])
        if b["tokens"] <= size or b["kind"] != "para":
            out.append(b)
            continue
        seg = text[b["start"]:b["end"]]
        pieces, last = [], 0
        for m in SENT_RE.finditer(seg):
            pieces.append((last, m.start()))
            last = m.end()
        pieces.append((last, len(seg)))
        for (a, z) in pieces:
            if seg[a:z].strip():
                out.append({"start": b["start"] + a, "end": b["start"] + z, "kind": "sent",
                            "tokens": ntok(seg[a:z])})
    return out


def pack_blocks(blocks, size, overlap):
    """Greedy packing; the tail of a chunk is carried into the next up to overlap tokens."""
    spans, cur, cur_t = [], [], 0
    for b in blocks:
        if cur and cur_t + b["tokens"] > size:
            spans.append((cur[0]["start"], cur[-1]["end"]))
            carry, ct = [], 0
            for pb in reversed(cur):
                if ct + pb["tokens"] > overlap:
                    break
                carry.insert(0, pb)
                ct += pb["tokens"]
            while carry and ct + b["tokens"] > size:
                ct -= carry[0]["tokens"]
                carry.pop(0)
            cur, cur_t = carry, ct
        cur.append(b)
        cur_t += b["tokens"]
    if cur:
        spans.append((cur[0]["start"], cur[-1]["end"]))
    return spans


def chunk_fixed(text, size, overlap):
    toks = list(TOKEN_RE.finditer(text))
    step = size - overlap
    spans, i = [], 0
    while i < len(toks):
        j = min(i + size, len(toks))
        spans.append((toks[i].start(), toks[j - 1].end()))
        if j == len(toks):
            break
        i += step
    return spans


def chunk_paragraph(text, lines, size, overlap):
    return pack_blocks(expand_blocks(text, build_blocks(lines), size), size, overlap)


def chunk_heading(text, lines, size, overlap, split_level):
    """One chunk per section; a section above size is repacked by paragraph."""
    ranges, begin = [], 0
    for i, (_s, _e, k, lv) in enumerate(lines):
        if k == "heading" and lv <= split_level and i > begin:
            ranges.append((begin, i))
            begin = i
    ranges.append((begin, len(lines)))
    spans = []
    for (a, z) in ranges:
        sect = [ln for ln in lines[a:z]]
        body = [ln for ln in sect if ln[2] != "blank"]
        if not body:
            continue
        start, end = body[0][0], body[-1][1]
        if ntok(text[start:end]) <= size:
            spans.append((start, end))
        else:
            spans.extend(pack_blocks(expand_blocks(text, build_blocks(sect), size), size, overlap))
    return spans


# ---------------------------------------------------------------- corpus

def collect_files(path):
    if os.path.isfile(path):
        return [(os.path.basename(path), path)]
    if not os.path.isdir(path):
        raise UsageError("path not found: " + path)
    found = []
    for root, dirs, names in os.walk(path):
        dirs.sort()
        for n in sorted(names):
            if n.lower().endswith(EXTENSIONS):
                full = os.path.join(root, n)
                found.append((os.path.relpath(full, path).replace(os.sep, "/"), full))
    return sorted(found)[:MAX_FILES]


def read_corpus(path):
    docs, skipped = [], []
    for rel, full in collect_files(path):
        try:
            if os.path.getsize(full) > MAX_FILE_BYTES:
                skipped.append({"file": rel, "reason": "larger than %d bytes" % MAX_FILE_BYTES})
                continue
            with open(full, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            skipped.append({"file": rel, "reason": "unreadable: %s" % exc.strerror})
            continue
        if b"\x00" in data:
            skipped.append({"file": rel, "reason": "binary content"})
            continue
        text = data.decode("utf-8-sig", errors="replace")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if not text.strip():
            skipped.append({"file": rel, "reason": "empty file"})
            continue
        docs.append({"source": rel, "text": text})
    if not docs:
        raise UsageError("no non-empty .md, .markdown or .txt files found under " + path)
    return docs, skipped


def overlaps_partially(spans, s, e):
    for (fs, fe) in spans:
        if fs < e and fe > s and not (s <= fs and fe <= e):
            return True
    return False


def build_chunks(docs, setting):
    chunks = []
    heading_files = 0
    for doc in docs:
        text = doc["text"]
        lines, headings, fence_spans, table_spans = scan_text(text)
        offsets, paths = heading_paths(headings)
        if headings:
            heading_files += 1
        strategy, size, overlap = setting["strategy"], setting["size"], setting["overlap"]
        if strategy == "fixed":
            spans = chunk_fixed(text, size, overlap)
        elif strategy == "paragraph":
            spans = chunk_paragraph(text, lines, size, overlap)
        else:
            spans = chunk_heading(text, lines, size, overlap, setting["split_level"])
        for n, (s, e) in enumerate(spans):
            body = text[s:e]
            first_line = body.lstrip().split("\n", 1)[0]
            path = path_at(offsets, paths, s)
            chunks.append({
                "id": "%s#%d" % (doc["source"], n), "source": doc["source"], "position": n,
                "start": s, "end": e, "text": body, "tokens": ntok(body),
                "heading_path": path, "file_has_headings": bool(headings),
                "starts_with_heading": bool(HEADING_RE.match(first_line)),
                "splits_fence": overlaps_partially(fence_spans, s, e),
                "splits_table": overlaps_partially(table_spans, s, e),
            })
    return chunks, heading_files


# ---------------------------------------------------------------- measuring

def percentile(sorted_values, p):
    return sorted_values[max(0, math.ceil(p * len(sorted_values)) - 1)]


def size_stats(chunks):
    values = sorted(c["tokens"] for c in chunks)
    labels = ["<%d" % HISTOGRAM_EDGES[0]]
    labels += ["%d-%d" % (a, b - 1) for a, b in zip(HISTOGRAM_EDGES, HISTOGRAM_EDGES[1:])]
    labels.append("%d+" % HISTOGRAM_EDGES[-1])
    hist = dict((lab, 0) for lab in labels)
    for v in values:
        hist[labels[bisect.bisect_right(HISTOGRAM_EDGES, v)]] += 1
    return {
        "chunks": len(values),
        "tokens": {"min": values[0], "median": round(statistics.median(values), 1),
                   "p95": percentile(values, 0.95), "max": values[-1],
                   "mean": round(sum(values) / len(values), 1)},
        "histogram": hist,
    }


def add_defect(defects, kind, severity, ids, note):
    if ids:
        defects.append({"type": kind, "severity": severity, "count": len(ids),
                        "examples": ids[:EXAMPLES_PER_DEFECT], "note": note})


def find_defects(chunks, setting, prefix_heading):
    defects = []
    size = setting["size"]
    if setting["overlap"] > size * MAX_OVERLAP_RATIO:
        add_defect(defects, "overlap_too_large", "error", ["overlap=%d size=%d" % (setting["overlap"], size)],
                   "overlap is above half the chunk size; most of each chunk repeats the previous one")
    add_defect(defects, "empty_chunk", "error", [c["id"] for c in chunks if not WORD_RE.search(c["text"])],
               "no letters or digits after cleaning")
    add_defect(defects, "split_code_fence", "error", [c["id"] for c in chunks if c["splits_fence"]],
               "chunk cuts through a fenced code block")
    add_defect(defects, "split_table", "error", [c["id"] for c in chunks if c["splits_table"]],
               "chunk cuts through a table")
    limit = size * OVERSIZE_FACTOR
    add_defect(defects, "oversize_chunk", "warn", [c["id"] for c in chunks if c["tokens"] > limit],
               "above %.0f tokens: an unsplittable block (code, table or sentence run)" % limit)
    min_tokens = setting["min_tokens"]
    add_defect(defects, "orphan_chunk", "warn", [c["id"] for c in chunks if c["tokens"] < min_tokens],
               "under %d tokens: rarely answers a question alone" % min_tokens)
    groups = {}
    for c in chunks:
        groups.setdefault(hashlib.sha256(norm(c["text"]).encode("utf-8")).hexdigest(), []).append(c["id"])
    dup_pairs = [g[0] + " == " + g[1] for g in groups.values() if len(g) > 1]
    extra = sum(len(g) - 1 for g in groups.values() if len(g) > 1)
    if extra:
        defects.append({"type": "duplicate_chunk", "severity": "warn", "count": extra,
                        "examples": dup_pairs[:EXAMPLES_PER_DEFECT],
                        "note": "identical text after whitespace and case folding; duplicates crowd out other results"})
    if not prefix_heading:
        lost = [c["id"] for c in chunks if c["file_has_headings"] and c["heading_path"] and not c["starts_with_heading"]]
        add_defect(defects, "heading_context_lost", "warn", lost,
                   "chunk starts inside a section, so its heading is absent from the indexed text; use --prefix-heading")
    return defects


def heading_context(chunks, heading_files, prefix_heading):
    in_files = [c for c in chunks if c["file_has_headings"]]
    with_path = [c for c in in_files if c["heading_path"]]
    mid = [c for c in with_path if not c["starts_with_heading"]]
    return {
        "files_with_headings": heading_files,
        "chunks_in_files_with_headings": len(in_files),
        "chunks_with_heading_path": len(with_path),
        "coverage": round(len(with_path) / len(in_files), 3) if in_files else None,
        "chunks_starting_mid_section": len(mid),
        "lost_in_indexed_text": 0 if prefix_heading else len(mid),
    }


# ---------------------------------------------------------------- retrieval

def load_questions(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as exc:
        raise UsageError("cannot read questions file %s: %s" % (path, exc))
    if isinstance(data, dict):
        data = data.get("questions")
    if not isinstance(data, list) or not data:
        raise UsageError("questions file must hold a non-empty JSON list of "
                         "{id, question, expected_passage, source?} objects")
    out = []
    for i, q in enumerate(data):
        if not isinstance(q, dict) or not isinstance(q.get("question"), str) or not isinstance(q.get("expected_passage"), str):
            raise UsageError("question %d needs string fields question and expected_passage" % (i + 1))
        out.append({"id": str(q.get("id", "q%d" % (i + 1))), "question": q["question"],
                    "passage": norm(q["expected_passage"]), "source": q.get("source")})
    return out


class Bm25:
    def __init__(self, texts):
        self.tf = [self._counts(t) for t in texts]
        self.lengths = [sum(tf.values()) for tf in self.tf]
        self.avg = (sum(self.lengths) / len(self.lengths)) or 1.0
        self.df = {}
        for tf in self.tf:
            for term in tf:
                self.df[term] = self.df.get(term, 0) + 1

    @staticmethod
    def _counts(text):
        counts = {}
        for w in WORD_RE.findall(text.lower()):
            counts[w] = counts.get(w, 0) + 1
        return counts

    def rank(self, query):
        n = len(self.tf)
        terms = set(WORD_RE.findall(query.lower()))
        scored = []
        for i, tf in enumerate(self.tf):
            score = 0.0
            for t in terms:
                f = tf.get(t, 0)
                if not f:
                    continue
                idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                score += idf * f * (BM25_K1 + 1) / (f + BM25_K1 * (1 - BM25_B + BM25_B * self.lengths[i] / self.avg))
            if score > 0:
                scored.append((-score, i))
        scored.sort()
        return [i for (_s, i) in scored]


def source_matches(wanted, source):
    return wanted is None or wanted == source or wanted == source.rsplit("/", 1)[-1]


def evaluate(chunks, docs, questions, ks, prefix_heading):
    index_texts = [(" ".join(c["heading_path"]) + " " + c["text"]) if prefix_heading else c["text"] for c in chunks]
    bm25 = Bm25(index_texts)
    chunk_norm = [norm(c["text"]) for c in chunks]
    doc_norm = dict((d["source"], norm(d["text"])) for d in docs)
    top_k = max(ks)
    hits = dict((k, 0) for k in ks)
    evaluated, not_in_corpus, boundary, missed, invalid = 0, [], [], [], []
    for q in questions:
        if len(q["passage"]) < MIN_PASSAGE_CHARS:
            invalid.append(q["id"])
            continue
        if not any(q["passage"] in txt for src, txt in doc_norm.items() if source_matches(q["source"], src)):
            not_in_corpus.append(q["id"])
            continue
        evaluated += 1
        relevant = set(i for i, c in enumerate(chunks)
                       if source_matches(q["source"], c["source"]) and q["passage"] in chunk_norm[i])
        if not relevant:
            boundary.append(q["id"])
            missed.append(q["id"])
            continue
        ranked = bm25.rank(q["question"])[:top_k]
        for k in ks:
            if any(i in relevant for i in ranked[:k]):
                hits[k] += 1
        if not any(i in relevant for i in ranked):
            missed.append(q["id"])
    return {
        "k": dict((str(k), round(hits[k] / evaluated, 3) if evaluated else None) for k in ks),
        "questions_evaluated": evaluated,
        "answer_spans_boundary": boundary,
        "missed_at_max_k": missed,
        "passage_not_in_corpus": not_in_corpus,
        "passage_too_short": invalid,
        "method": "stdlib BM25 over chunk text; ranks settings against each other, not a production retriever",
    }


# ---------------------------------------------------------------- commands

def make_setting(strategy, size, overlap, args):
    if strategy not in STRATEGIES:
        raise UsageError("strategy must be one of %s, got %r" % (", ".join(STRATEGIES), strategy))
    if size < 1 or overlap < 0:
        raise UsageError("size must be at least 1 and overlap at least 0")
    if overlap >= size:
        raise UsageError("overlap must be smaller than size (got overlap %d, size %d)" % (overlap, size))
    return {"strategy": strategy, "size": size, "overlap": overlap, "min_tokens": args.min_tokens,
            "split_level": args.split_level, "prefix_heading": bool(args.prefix_heading),
            "token_unit": "word or punctuation mark"}


def parse_ks(text):
    try:
        ks = sorted(set(int(x) for x in text.split(",") if x.strip()))
    except ValueError:
        raise UsageError("--k must be comma separated integers, for example 1,3,5")
    if not ks or ks[0] < 1:
        raise UsageError("--k values must be at least 1")
    return ks


def run_setting(docs, setting, questions, ks):
    chunks, heading_files = build_chunks(docs, setting)
    prefix = setting["prefix_heading"]
    defects = find_defects(chunks, setting, prefix)
    recall = None
    if questions is not None:
        recall = evaluate(chunks, docs, questions, ks, prefix)
        if recall["answer_spans_boundary"]:
            add_defect(defects, "answer_spans_boundary", "warn", recall["answer_spans_boundary"],
                       "question's expected passage is in the corpus but in no single chunk")
    return chunks, {"settings": setting, "stats": size_stats(chunks),
                    "heading_context": heading_context(chunks, heading_files, prefix),
                    "defects": defects, "recall_at_k": recall}


def emit(report):
    sys.stdout.write(json.dumps(report, indent=2, allow_nan=False) + "\n")


def has_error(defects):
    return any(d["severity"] == "error" for d in defects)


def cmd_plan(args):
    setting = make_setting(args.strategy, args.size, args.overlap, args)
    docs, skipped = read_corpus(args.path)
    questions = load_questions(args.questions) if args.questions else None
    ks = parse_ks(args.k)
    if args.out:
        src = os.path.normcase(os.path.realpath(args.path))
        dst = os.path.normcase(os.path.realpath(args.out))
        if dst == src or (os.path.isdir(args.path) and dst.startswith(src.rstrip(os.sep) + os.sep)):
            raise UsageError("--out %s is the input corpus or inside it; choose a path outside it (--force does not override this)" % args.out)
    if args.out and os.path.exists(args.out) and not args.force:
        raise UsageError("%s exists; pass --force to overwrite it" % args.out)
    chunks, report = run_setting(docs, setting, questions, ks)
    report = dict([("command", "plan"), ("files", len(docs)), ("skipped", skipped)] + list(report.items()))
    report["output_file"] = None
    if args.out:
        try:
            with open(args.out, "w", encoding="utf-8", newline="\n") as fh:
                for c in chunks:
                    fh.write(json.dumps({"id": c["id"], "source": c["source"], "position": c["position"],
                                         "heading_path": c["heading_path"], "tokens": c["tokens"],
                                         "start": c["start"], "end": c["end"], "text": c["text"]},
                                        allow_nan=False) + "\n")
        except OSError as exc:
            raise UsageError("cannot write %s: %s" % (args.out, exc.strerror))
        report["output_file"] = args.out
    emit(report)
    return 1 if has_error(report["defects"]) else 0


def parse_setting(text, args):
    parts = text.split(":")
    if len(parts) != 3:
        raise UsageError("--setting must look like strategy:size:overlap, got %r" % text)
    try:
        return make_setting(parts[0], int(parts[1]), int(parts[2]), args)
    except ValueError:
        raise UsageError("--setting size and overlap must be integers, got %r" % text)


def cmd_compare(args):
    if len(args.setting) < 2:
        raise UsageError("compare needs at least two --setting values")
    docs, skipped = read_corpus(args.path)
    questions = load_questions(args.questions)
    ks = parse_ks(args.k)
    runs = []
    for text in args.setting:
        setting = parse_setting(text, args)
        _chunks, rep = run_setting(docs, setting, questions, ks)
        runs.append({
            "label": text, "settings": setting, "chunks": rep["stats"]["chunks"],
            "tokens": rep["stats"]["tokens"],
            "defect_counts": dict((d["type"], d["count"]) for d in rep["defects"]),
            "has_error_defect": has_error(rep["defects"]),
            "recall_at_k": rep["recall_at_k"]["k"], "answer_spans_boundary": rep["recall_at_k"]["answer_spans_boundary"],
        })
    big, small = str(max(ks)), str(min(ks))
    order = sorted(range(len(runs)), key=lambda i: (-(runs[i]["recall_at_k"][big] or 0),
                                                    -(runs[i]["recall_at_k"][small] or 0),
                                                    runs[i]["has_error_defect"], runs[i]["chunks"], i))
    emit({"command": "compare", "files": len(docs), "skipped": skipped, "k": ks, "runs": runs,
          "ranking": [runs[i]["label"] for i in order],
          "note": "ranking is by BM25 recall at the largest k, then the smallest k, then no error defects, then fewer chunks"})
    return 1 if any(r["has_error_defect"] for r in runs) else 0


def build_parser():
    p = argparse.ArgumentParser(prog="plan_chunks.py", description="Chunk Markdown or text and measure the result.")
    sub = p.add_subparsers(dest="command", required=True)
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("path", help="a file, or a folder searched recursively")
    common.add_argument("--min-tokens", type=int, default=DEFAULT_MIN_TOKENS)
    common.add_argument("--split-level", type=int, default=3, help="heading strategy: split at headings up to this level")
    common.add_argument("--prefix-heading", action="store_true", help="index the heading path together with each chunk")
    common.add_argument("--k", default="1,3,5")
    plan = sub.add_parser("plan", parents=[common])
    plan.add_argument("--strategy", choices=STRATEGIES, default="paragraph")
    plan.add_argument("--size", type=int, default=400)
    plan.add_argument("--overlap", type=int, default=40)
    plan.add_argument("--questions")
    plan.add_argument("--out")
    plan.add_argument("--force", action="store_true")
    cmp_ = sub.add_parser("compare", parents=[common])
    cmp_.add_argument("--questions", required=True)
    cmp_.add_argument("--setting", action="append", default=[], help="strategy:size:overlap, repeat for each setting")
    return p


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        args = build_parser().parse_args(argv)
        if args.split_level < 1 or args.split_level > 6:
            raise UsageError("--split-level must be between 1 and 6")
        return cmd_plan(args) if args.command == "plan" else cmd_compare(args)
    except UsageError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
