import "./Mascot.css";

interface MascotProps {
  size?: number;
  className?: string;
  wave?: boolean;
  bounce?: boolean;
}

/**
 * An original, simple cartoon bulldog mascot — built from basic shapes,
 * not traced or adapted from any real school's logo or mascot artwork.
 * Colors come from the site's own navy/gold palette rather than any
 * specific team's colors.
 */
export default function Mascot({ size = 120, className, wave = true, bounce = true }: MascotProps) {
  const classes = ["mascot", bounce ? "mascot--bounce" : "", className ?? ""].filter(Boolean).join(" ");

  return (
    <svg
      className={classes}
      width={size}
      height={size}
      viewBox="0 0 200 200"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-label="Campus Customs mascot, a friendly cartoon bulldog"
    >
      {/* body */}
      <ellipse cx="100" cy="150" rx="48" ry="34" fill="var(--cc-navy)" />
      {/* chest patch */}
      <ellipse cx="100" cy="158" rx="22" ry="16" fill="var(--cc-white)" />
      {/* back legs */}
      <ellipse cx="66" cy="176" rx="12" ry="10" fill="var(--cc-navy)" />
      <ellipse cx="134" cy="176" rx="12" ry="10" fill="var(--cc-navy)" />

      {/* waving front paw */}
      <g className={wave ? "mascot__paw mascot__paw--wave" : "mascot__paw"} style={{ transformOrigin: "138px 128px" }}>
        <ellipse cx="138" cy="118" rx="11" ry="16" fill="var(--cc-navy)" />
        <circle cx="138" cy="106" r="7" fill="var(--cc-white)" />
      </g>
      {/* still front paw */}
      <ellipse cx="72" cy="128" rx="11" ry="16" fill="var(--cc-navy)" />

      {/* head */}
      <circle cx="100" cy="92" r="46" fill="var(--cc-navy)" />
      {/* ears */}
      <ellipse cx="62" cy="68" rx="14" ry="20" transform="rotate(-20 62 68)" fill="var(--cc-navy-dark)" />
      <ellipse cx="138" cy="68" rx="14" ry="20" transform="rotate(20 138 68)" fill="var(--cc-navy-dark)" />

      {/* muzzle */}
      <ellipse cx="100" cy="104" rx="26" ry="20" fill="var(--cc-white)" />
      {/* eyes */}
      <circle cx="84" cy="84" r="5.5" fill="var(--cc-white)" />
      <circle cx="116" cy="84" r="5.5" fill="var(--cc-white)" />
      <circle cx="85" cy="85" r="2.6" fill="var(--cc-navy-dark)" />
      <circle cx="117" cy="85" r="2.6" fill="var(--cc-navy-dark)" />
      {/* nose */}
      <ellipse cx="100" cy="98" rx="8" ry="6" fill="var(--cc-navy-dark)" />
      {/* smile */}
      <path
        d="M 88 110 Q 100 118 112 110"
        stroke="var(--cc-navy-dark)"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />

      {/* collar + gold star tag */}
      <path d="M 66 122 Q 100 136 134 122" stroke="var(--cc-gold)" strokeWidth="10" fill="none" />
      <circle cx="100" cy="132" r="7" fill="var(--cc-gold)" />
    </svg>
  );
}
