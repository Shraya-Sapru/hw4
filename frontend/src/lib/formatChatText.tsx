import type { ReactNode } from "react";

// The agent's replies often come back with light markdown — **bold**
// and "- " bullet lines — since that's the model's default writing
// style. Left as raw text, those symbols show up literally in the chat
// bubble and make it harder to read. This renders just enough markdown
// (bold text and bullet lists) to look like normal prose, without
// pulling in a full markdown library for what's a pretty small need.

function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts
    .filter((part) => part !== "")
    .map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={`${keyPrefix}-${i}`}>{part.slice(2, -2)}</strong>;
      }
      return <span key={`${keyPrefix}-${i}`}>{part}</span>;
    });
}

export function formatChatText(text: string): ReactNode {
  const lines = text.split("\n").map((line) => line.trim());

  const blocks: ReactNode[] = [];
  let bulletBuffer: string[] = [];

  function flushBullets(key: string) {
    if (bulletBuffer.length === 0) return;
    blocks.push(
      <ul className="chat-widget__bubble-list" key={`ul-${key}`}>
        {bulletBuffer.map((item, i) => (
          <li key={`li-${key}-${i}`}>{renderInline(item, `li-${key}-${i}`)}</li>
        ))}
      </ul>
    );
    bulletBuffer = [];
  }

  lines.forEach((line, i) => {
    const bulletMatch = /^[-•]\s+(.*)$/.exec(line);
    if (bulletMatch) {
      bulletBuffer.push(bulletMatch[1]);
      return;
    }
    flushBullets(String(i));
    if (line === "") return; // collapse blank lines rather than rendering empty paragraphs
    blocks.push(<p key={`p-${i}`}>{renderInline(line, `p-${i}`)}</p>);
  });
  flushBullets("end");

  return <>{blocks}</>;
}
