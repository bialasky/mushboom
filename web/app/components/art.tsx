type StillProps = {
  score: number;
};

export function MushroomMark() {
  return (
    <svg className="mark" viewBox="0 0 32 32" aria-hidden="true">
      <path d="M4 20.2C4 12 9.2 6 16 6s12 6 12 14.2H4Z" fill="#c4784a" />
      <path d="M10 11.5c2.2-3 6.4-3.6 9.4-1.2.2 2.4-2.2 3.2-5.2 2.4-2.2-.6-3.4-.8-4.2-1.2Z" fill="#f3d2b0" opacity="0.8" />
      <ellipse cx="16" cy="20.2" rx="12" ry="3.3" fill="#6e3a22" />
      <path d="M6.2 19.4c3.2 1.5 6.8.5 9.8-.3 3 .8 6.6 1.8 9.8.3" stroke="#e6c56a" strokeWidth="1.25" fill="none" />
      <path d="M12.4 21c-.35 3.4-.9 6.6-.7 8.6h8.6c.2-2-.35-5.2-.7-8.6" fill="#f4e7cc" />
      <path d="M13.2 24.2h5.6M13.4 27.2h5.2" stroke="#c4a574" strokeWidth="0.7" />
    </svg>
  );
}

export function FlushStill({ score }: StillProps) {
  const lively = score >= 48;
  const flush = score >= 72;
  return (
    <svg className="still" viewBox="0 0 168 140" aria-hidden="true">
      <ellipse cx="86" cy="128" rx="62" ry="8" fill="#0c100b" opacity="0.55" />
      {lively ? <Chanterelle /> : null}
      <Bolete x={46} y={4} />
      {flush ? <Bolete x={112} y={38} scale={0.58} /> : null}
    </svg>
  );
}

export function Canopy() {
  return (
    <svg className="canopy" viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <g fill="#c9cdbe">
        <circle cx="90" cy="70" r="1.6" opacity="0.35" />
        <circle cx="210" cy="140" r="1.2" opacity="0.22" />
        <circle cx="340" cy="48" r="2" opacity="0.2" />
        <circle cx="520" cy="110" r="1.3" opacity="0.28" />
        <circle cx="760" cy="64" r="1.8" opacity="0.18" />
        <circle cx="980" cy="130" r="1.2" opacity="0.3" />
        <circle cx="1180" cy="56" r="2.1" opacity="0.22" />
        <circle cx="1320" cy="160" r="1.4" opacity="0.26" />
        <circle cx="150" cy="240" r="1.1" opacity="0.16" />
        <circle cx="1280" cy="280" r="1.5" opacity="0.14" />
      </g>
    </svg>
  );
}

export function RainIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M4.6 1.6c1.7 2.3 2.5 3.6 2.5 4.8a2.5 2.5 0 0 1-5 0c0-1.2.8-2.5 2.5-4.8Z" fill="currentColor" />
      <path d="M11.2 5.2c1.5 2.1 2.2 3.2 2.2 4.3a2.2 2.2 0 0 1-4.4 0c0-1.1.7-2.2 2.2-4.3Z" fill="currentColor" />
    </svg>
  );
}

export function NightIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M9.4 1.6A5.6 5.6 0 1 0 14 9.6 4.7 4.7 0 0 1 9.4 1.6Z" fill="currentColor" />
    </svg>
  );
}

export function DropIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <path d="M8 1.4c2.6 3.4 3.9 5.3 3.9 7.4a3.9 3.9 0 0 1-7.8 0c0-2.1 1.3-4 3.9-7.4Z" fill="currentColor" />
    </svg>
  );
}

function Bolete({ x, y, scale = 1 }: { x: number; y: number; scale?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`}>
      <path d="M6 66C6 32 22 8 44 8s38 24 38 58H6Z" fill="#b4633a" />
      <path d="M20 28c8-12 26-14 38-4 1 8-8 12-18 9-8-2-15-2-20-5Z" fill="#f0c7a2" opacity="0.72" />
      <ellipse cx="44" cy="66" rx="38" ry="11" fill="#6a3420" />
      <path d="M12 63c10 8 54 8 64 0" stroke="#e7c56b" strokeWidth="1.6" fill="none" />
      <path d="M16 68c8 5 48 5 56 0" stroke="#e7c56b" strokeWidth="1" fill="none" opacity="0.55" />
      <path d="M30 70c-2 16-5 34-2 50h32c3-16 0-34-2-50" fill="#f6ead0" />
      <path d="M33 84h22M34 98h20M35 110h18" stroke="#c6a56e" strokeWidth="1.1" opacity="0.8" />
    </g>
  );
}

function Chanterelle() {
  return (
    <g transform="translate(4 46)">
      <path d="M8 46c2-18 12-32 24-32 6 10 2 20-4 26 8-2 18 2 20 12-14 8-30 10-40-6Z" fill="#e2a322" />
      <path d="M22 40c6 2 14 2 18 8" stroke="#f6d98a" strokeWidth="1.4" fill="none" />
      <path d="M20 44c-1 12-2 22-1 32h10c1-10 0-20-1-32" fill="#f3d48a" />
    </g>
  );
}
