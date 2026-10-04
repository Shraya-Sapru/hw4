# Campus Customs — Design Pass

What changed, grouped by area, with a one-sentence reason each is expected to help someone
actually stay on the site and buy something.

## Fonts

Added **Fredoka** (a bold, rounded display face) for every headline, paired with **Inter** for
all body text — replacing the previous generic serif/system-font mix. A distinctive, friendly
headline font is what makes a storefront feel like a real brand instead of a template, which is
the first thing that earns a new visitor's trust enough to keep browsing.

## Colors

Added a warm gold accent (`--cc-gold` / `--cc-gold-dark`) alongside the existing navy, used
specifically for primary buttons, hover states, and small decorative touches (sparkles, the
mascot's collar) — the rest of the palette (navy, cream, white) is unchanged. A single consistent
accent color draws the eye straight to the actions that matter (Shop All, Create account, Send)
instead of leaving every element competing for attention equally.

## Layout & spacing

Reworked the Home hero into a two-column layout (copy beside the mascot) instead of stacked
text alone, and gave the About Us page real section rhythm — hero, story, values grid, timeline,
visit block — instead of one long column of paragraphs. Clear visual sections make a page feel
navigable rather than like a wall of text, which matters directly for whether someone scrolls
further or bounces.

## Motion

Added a handful of small, purposeful animations: the mascot bounces and waves, hero/product-card
hover states include a brief light "shine" sweep and a small sparkle (confined to the image area
so it never overlaps text), About Us sections fade/slide in as they scroll into view, and the
chat typing indicator is three animated dots instead of static text. Every one of these is
disabled via a single global `prefers-reduced-motion: reduce` rule (plus a JS check in the
scroll-reveal component, so content isn't left invisible for anyone who's asked for reduced
motion). Motion used this sparingly draws attention to the right moments (a button is
clickable, a reply has arrived) without being distracting or excluding anyone who's sensitive to it.

## Mascot

Added an original SVG bulldog mascot (`components/Mascot.tsx`) — built from simple shapes in the
site's own navy/gold palette, not traced or adapted from any real school's logo or mascot
artwork. It appears bouncing in the Home hero, waving in the About Us header, and as the
chatbot's avatar. A recognizable, friendly character gives the brand a face — it's a big part of
what makes a storefront feel approachable rather than purely transactional.

## Product presentation

The Home page's "Fan Favorites" now pulls real products from the live backend (`/api/products`)
instead of the hardcoded mock data it originally shipped with — real images, names, and prices,
and clicking through still lands on that product's real detail page via the same `CatalogueCard`
component used on the Products page. Showing genuine, currently-in-catalogue items (not
placeholder examples) is what makes "Fan Favorites" a believable reason to click through to Shop
All, rather than something that quietly stops matching what the store actually sells.

## Chat panel

Re-skinned the chat panel to match the rest of the brand: the mascot as the assistant's avatar,
a navy gradient header, rounded message bubbles, a gold send button, and a proper three-dot
typing indicator in place of static "Thinking…" text. Also fixed a real readability problem: chat
replies were showing raw `**bold**` and `- bullet` markdown symbols literally in the bubble,
since the panel only ever rendered plain text. Added a small formatter
(`lib/formatChatText.tsx`) that renders bold text and bullet lists properly, and told the system
prompt what the panel can and can't display, so lists of products or sizes read as normal,
polished sentences instead of looking like unrendered markup. A chat panel that looks and reads
like part of the same store — not a bolted-on widget — is more likely to actually get used
instead of ignored, which is the whole point of having it.
