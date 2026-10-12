type PhotoProps = {
  className?: string;
};

export function ForestPhoto({ className }: PhotoProps) {
  return <img className={className} src="/forest-moss.webp" alt="" />;
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
