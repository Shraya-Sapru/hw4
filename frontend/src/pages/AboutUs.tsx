import Mascot from "../components/Mascot";
import Reveal from "../components/Reveal";
import "./AboutUs.css";

const VALUES = [
  {
    title: "Community First",
    text: "We're run by people from this campus, for this campus — not a faceless souvenir counter.",
    icon: (
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <path
          d="M24 40 C12 32 6 24 6 16 C6 10 11 6 16 6 C19.5 6 22.5 8 24 11 C25.5 8 28.5 6 32 6 C37 6 42 10 42 16 C42 24 36 32 24 40 Z"
          fill="var(--cc-gold)"
        />
      </svg>
    ),
  },
  {
    title: "Real Quality",
    text: "Small batches, trusted blanks, and prints that survive more than one wash.",
    icon: (
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <path
          d="M24 4 L29 18 L44 18 L32 27 L36.5 42 L24 33 L11.5 42 L16 27 L4 18 L19 18 Z"
          fill="var(--cc-gold)"
        />
      </svg>
    ),
  },
  {
    title: "Campus Spirit",
    text: "From move-in day to homecoming decades later, we keep the pride stitched in.",
    icon: (
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <circle cx="24" cy="24" r="16" fill="var(--cc-white)" />
        <circle cx="24" cy="24" r="7" fill="var(--cc-gold)" />
      </svg>
    ),
  },
];

const TIMELINE = [
  {
    year: "Year One",
    text: "A folding table outside the student union, a box of hoodies, and a lot of homemade enthusiasm.",
  },
  {
    year: "Year Two",
    text: "Word got around. The folding table became a real storefront, and alumni started mailing us requests from out of state.",
  },
  {
    year: "This Year",
    text: "We brought the whole catalogue online — and gave our shopping assistant a voice, so finding the right gear is as easy as asking.",
  },
];

export default function AboutUs() {
  return (
    <div className="about">
      <section className="about__hero">
        <span className="about__hero-sparkle about__hero-sparkle--1" aria-hidden="true">
          ✦
        </span>
        <span className="about__hero-sparkle about__hero-sparkle--2" aria-hidden="true">
          ✦
        </span>
        <span className="about__hero-sparkle about__hero-sparkle--3" aria-hidden="true">
          ✦
        </span>
        <p className="about__eyebrow">Our Story</p>
        <h1>BIG PRIDE. BUILT ON CAMPUS.</h1>
        <div className="about__hero-mascot">
          <Mascot size={110} />
        </div>
      </section>

      <Reveal className="about__content">
        <p>
          Campus Customs started as a folding table outside the student
          union and grew into the place our whole community comes back to
          for gear that actually feels like home. We're not a big-box
          souvenir shop — we're run by people who sat in the same lecture
          halls, cheered from the same bleachers, and still get a little
          emotional every homecoming weekend.
        </p>
        <p>
          Every hoodie, tee, and crewneck we carry is picked with one
          question in mind: would we actually wear this after graduation?
          That's why you'll find pieces for current students pulling
          all-nighters in the library, alumni showing off their colors
          decades later, and die-hard fans who've never missed a home
          game.
        </p>
      </Reveal>

      <section className="about__values">
        <Reveal>
          <h2 className="about__section-title">What We Care About</h2>
        </Reveal>
        <div className="about__values-grid">
          {VALUES.map((value, i) => (
            <Reveal key={value.title} delayMs={i * 120}>
              <div className="about__value-card">
                <div className="about__value-icon">{value.icon}</div>
                <h3>{value.title}</h3>
                <p>{value.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <section className="about__timeline-section">
        <Reveal>
          <h2 className="about__section-title">Our Story So Far</h2>
        </Reveal>
        <div className="about__timeline">
          {TIMELINE.map((entry, i) => (
            <Reveal key={entry.year} delayMs={i * 150} className="about__timeline-entry">
              <div className="about__timeline-dot" aria-hidden="true" />
              <div>
                <p className="about__timeline-year">{entry.year}</p>
                <p>{entry.text}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      <Reveal className="about__visit">
        <svg className="about__storefront" viewBox="0 0 220 140" aria-hidden="true">
          <rect x="30" y="50" width="160" height="80" rx="4" fill="var(--cc-white)" opacity="0.1" />
          <rect x="30" y="50" width="160" height="80" rx="4" stroke="var(--cc-gold)" strokeWidth="3" fill="none" />
          <path d="M20 50 L110 20 L200 50 Z" fill="var(--cc-gold)" />
          <rect x="95" y="80" width="30" height="50" fill="var(--cc-gold)" />
          <circle cx="118" cy="105" r="2.5" fill="var(--cc-navy-dark)" />
          <rect x="45" y="68" width="30" height="28" rx="2" fill="var(--cc-gold)" opacity="0.85" />
          <rect x="145" y="68" width="30" height="28" rx="2" fill="var(--cc-gold)" opacity="0.85" />
        </svg>
        <h2 className="about__section-title about__section-title--light">Come Visit Us</h2>
        <p>
          Prefer to see the fabric and try your size before you buy? Swing
          by our shop near the heart of campus — pull up a chair, say hi,
          and let us know what you're looking for. We're usually around
          most afternoons, and always happy for an excuse to talk school
          spirit.
        </p>
      </Reveal>
    </div>
  );
}
