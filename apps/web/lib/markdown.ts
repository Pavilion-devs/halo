// Minimal, self-contained markdown parser for Halo's live agent recommendations.
// The agent emits free-form GitHub-flavoured markdown (headings, numbered lists,
// tables, callouts) — we parse it to a typed block tree so the renderer can map
// each block onto the dark-console design system. Inline formatting stays as raw
// strings and is resolved at render time (see components/war-room/markdown-view.tsx).

export type MdBlock =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "list"; ordered: boolean; items: string[] }
  | { type: "table"; header: string[] | null; rows: string[][] }
  | { type: "callout"; text: string }
  | { type: "code"; text: string }
  | { type: "hr" };

// Strip leading decorative glyphs so headings/callouts read cleanly: whitespace,
// emoji + their variation selectors (U+FE00-FE0F) / ZWJ (U+200D) / keycap combiner
// (U+20E3), bullets (U+2022/25AA/25E6), dashes, middot (U+00B7), blockquote markers.
const LEAD_DECOR =
  /^[\s\p{Extended_Pictographic}\uFE00-\uFE0F\u200D\u20E3\u2022\u25AA\u25E6\u2013\u2014\u00B7>-]+/u;
const stripLead = (value: string): string => value.replace(LEAD_DECOR, "").trim();

const HEADING = /^(#{1,6})\s+(.*)$/;
const ORDERED = /^\s*\d+[.)]\s+(.*)$/;
const UNORDERED = /^\s*[-*+]\s+(.*)$/;
const HR = /^(-{3,}|\*{3,}|_{3,})$/;
const FENCE = /^```/;
const CALLOUT_LEAD = /^(?:>|\p{Extended_Pictographic}|(?:warning|caution|note|important)\s*:)/iu;

export function normalizeMarkdown(raw: string): string {
  return raw
    .replace(/\r\n?/g, "\n")
    .replace(/�/g, "") // drop upstream mojibake (mangled emoji)
    .replace(/[ \t]+$/gm, "")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

const splitRow = (line: string): string[] =>
  line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());

const isSeparatorRow = (cells: string[]): boolean =>
  cells.length > 0 && cells.every((cell) => /^:?-{1,}:?$/.test(cell));

export function parseMarkdown(normalized: string): MdBlock[] {
  const lines = normalized.split("\n");
  const blocks: MdBlock[] = [];
  let i = 0;

  // A real GFM table either has pipe-delimited rows (leading "|") or a header
  // line immediately followed by a separator row. Prose with inline pipes (e.g.
  // "**Incident:** x | **Product:** y") must NOT qualify, or it derails parsing.
  const looksLikeTable = (idx: number): boolean => {
    const first = lines[idx];
    if (!first || !first.includes("|")) return false;
    if (first.trim().startsWith("|")) return true;
    const next = lines[idx + 1];
    return Boolean(next && next.includes("|") && isSeparatorRow(splitRow(next)));
  };

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    if (trimmed === "") {
      i += 1;
      continue;
    }

    // fenced code
    if (FENCE.test(trimmed)) {
      const body: string[] = [];
      i += 1;
      while (i < lines.length && !FENCE.test(lines[i].trim())) {
        body.push(lines[i]);
        i += 1;
      }
      i += 1; // closing fence
      blocks.push({ type: "code", text: body.join("\n") });
      continue;
    }

    if (HR.test(trimmed)) {
      blocks.push({ type: "hr" });
      i += 1;
      continue;
    }

    const heading = trimmed.match(HEADING);
    if (heading) {
      blocks.push({ type: "heading", level: heading[1].length, text: stripLead(heading[2]) });
      i += 1;
      continue;
    }

    // table
    if (looksLikeTable(i)) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].includes("|") && lines[i].trim() !== "") {
        tableLines.push(lines[i]);
        i += 1;
      }
      const rows = tableLines.map(splitRow);
      const sepIndex = rows.findIndex(isSeparatorRow);
      const header = sepIndex >= 1 ? rows[sepIndex - 1] : null;
      const body = rows.filter((row, index) => !isSeparatorRow(row) && index !== sepIndex - 1);
      blocks.push({ type: "table", header, rows: body });
      continue;
    }

    // lists
    if (ORDERED.test(line) || UNORDERED.test(line)) {
      const ordered = ORDERED.test(line);
      const matcher = ordered ? ORDERED : UNORDERED;
      const items: string[] = [];
      while (i < lines.length && matcher.test(lines[i])) {
        items.push(lines[i].match(matcher)![1].trim());
        i += 1;
      }
      blocks.push({ type: "list", ordered, items });
      continue;
    }

    // callout — a warning/blockquote line plus the prose that follows it
    if (CALLOUT_LEAD.test(trimmed)) {
      const body: string[] = [];
      while (i < lines.length && lines[i].trim() !== "" && !HEADING.test(lines[i].trim())) {
        body.push(lines[i].replace(/^>\s?/, ""));
        i += 1;
      }
      blocks.push({ type: "callout", text: stripLead(body.join(" ")) });
      continue;
    }

    // paragraph — gather until a blank line or a new block starts
    const para: string[] = [];
    while (i < lines.length) {
      const current = lines[i];
      const ct = current.trim();
      if (
        ct === "" ||
        HEADING.test(ct) ||
        HR.test(ct) ||
        FENCE.test(ct) ||
        ORDERED.test(current) ||
        UNORDERED.test(current) ||
        CALLOUT_LEAD.test(ct) ||
        looksLikeTable(i)
      ) {
        break;
      }
      para.push(ct);
      i += 1;
    }
    if (para.length > 0) {
      blocks.push({ type: "paragraph", text: para.join(" ") });
    } else {
      i += 1; // safety: never stall on an unforeseen line shape
    }
  }

  return blocks;
}

// Parse a recommendation, peeling off the agent's boilerplate title banner (it
// leads with a top-level "… Incident Commander — Assessment" heading at # or ##)
// since the card already carries a "Halo's read" header.
export function splitRecommendation(raw: string | null | undefined): MdBlock[] {
  if (!raw || !raw.trim()) return [];
  const blocks = parseMarkdown(normalizeMarkdown(raw));
  if (blocks.length > 0 && blocks[0].type === "heading" && blocks[0].level <= 2) {
    return blocks.slice(1);
  }
  return blocks;
}
