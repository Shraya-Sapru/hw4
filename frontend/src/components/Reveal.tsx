import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";
import "./Reveal.css";

interface RevealProps {
  children: ReactNode;
  className?: string;
  delayMs?: number;
}

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

/** Fades/slides its children in once they scroll into view. Shows
 * content immediately, with no animation, for anyone who's asked their
 * system for reduced motion — this is the one place that preference has
 * to be checked in JS rather than CSS, since otherwise the element would
 * stay invisible forever (the "hidden until revealed" state has to not
 * apply at all, not just animate instantly). */
export default function Reveal({ children, className, delayMs = 0 }: RevealProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(() => prefersReducedMotion());

  useEffect(() => {
    if (prefersReducedMotion() || visible) return;
    const node = ref.current;
    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setVisible(true);
          observer.disconnect();
        }
      },
      { threshold: 0.15 }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [visible]);

  return (
    <div
      ref={ref}
      className={["reveal", visible ? "reveal--visible" : "", className ?? ""].filter(Boolean).join(" ")}
      style={{ transitionDelay: visible ? `${delayMs}ms` : undefined }}
    >
      {children}
    </div>
  );
}
