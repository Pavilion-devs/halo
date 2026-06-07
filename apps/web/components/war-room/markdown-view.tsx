import { AlertTriangle } from "lucide-react";
import type { ReactNode } from "react";

import type { MdBlock } from "@/lib/markdown";

type Props = {
  blocks: MdBlock[];
};

// Inline formatting: bold and inline code only. Single-asterisk emphasis and
// underscores are intentionally unsupported — incident text is full of tokens
// like `sk-*` and `halo_vm_normal` that would be mangled by greedy emphasis.
const INLINE = /(\*\*([^*]+)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\))/g;

function renderInline(text: string, keyBase: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex = 0;
  let token = 0;
  let match: RegExpExecArray | null;

  INLINE.lastIndex = 0;
  while ((match = INLINE.exec(text)) !== null) {
    if (match.index > lastIndex) nodes.push(text.slice(lastIndex, match.index));
    const key = `${keyBase}-${token++}`;
    if (match[2] !== undefined) {
      nodes.push(<strong key={key}>{match[2]}</strong>);
    } else if (match[3] !== undefined) {
      nodes.push(
        <code key={key} className="md-code">
          {match[3]}
        </code>
      );
    } else if (match[4] !== undefined) {
      nodes.push(
        <a key={key} href={match[5]} className="md-link" target="_blank" rel="noreferrer">
          {match[4]}
        </a>
      );
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) nodes.push(text.slice(lastIndex));
  return nodes;
}

export function MarkdownView({ blocks }: Props) {
  return (
    <div className="memo-markdown">
      {blocks.map((block, index) => {
        const key = `b-${index}`;
        switch (block.type) {
          case "heading": {
            const level = Math.min(Math.max(block.level, 2), 4);
            const Tag = `h${level}` as "h2" | "h3" | "h4";
            return (
              <Tag key={key} className={`md-h md-h${level}`}>
                {renderInline(block.text, key)}
              </Tag>
            );
          }
          case "paragraph":
            return (
              <p key={key} className="md-p">
                {renderInline(block.text, key)}
              </p>
            );
          case "list":
            return block.ordered ? (
              <ol key={key} className="md-list md-ol">
                {block.items.map((item, i) => (
                  <li key={`${key}-${i}`}>{renderInline(item, `${key}-${i}`)}</li>
                ))}
              </ol>
            ) : (
              <ul key={key} className="md-list md-ul">
                {block.items.map((item, i) => (
                  <li key={`${key}-${i}`}>{renderInline(item, `${key}-${i}`)}</li>
                ))}
              </ul>
            );
          case "table":
            return (
              <div key={key} className="md-table-wrap">
                <table className="md-table">
                  {block.header ? (
                    <thead>
                      <tr>
                        {block.header.map((cell, c) => (
                          <th key={`${key}-h-${c}`}>{renderInline(cell, `${key}-h-${c}`)}</th>
                        ))}
                      </tr>
                    </thead>
                  ) : null}
                  <tbody>
                    {block.rows.map((row, r) => (
                      <tr key={`${key}-r-${r}`}>
                        {row.map((cell, c) => (
                          <td key={`${key}-r-${r}-${c}`}>{renderInline(cell, `${key}-r-${r}-${c}`)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            );
          case "callout":
            return (
              <div key={key} className="md-callout">
                <AlertTriangle size={16} strokeWidth={2.2} aria-hidden />
                <div>{renderInline(block.text, key)}</div>
              </div>
            );
          case "code":
            return (
              <pre key={key} className="md-pre">
                <code>{block.text}</code>
              </pre>
            );
          case "hr":
            return <hr key={key} className="md-hr" />;
          default:
            return null;
        }
      })}
    </div>
  );
}
