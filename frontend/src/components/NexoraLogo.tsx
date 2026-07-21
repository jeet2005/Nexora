interface Props {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'hero';
}

const VIEWBOX = '0 0 810 83';
const SVG_SIZES = {
  sm: 110,
  md: 148,
  lg: 210,
  hero: 370,
};

export default function NexoraLogo({ className = '', size = 'md' }: Props) {
  const width = SVG_SIZES[size];
  const height = (width * 83) / 810;

  return (
    <svg
      width={width}
      height={height}
      viewBox={VIEWBOX}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Nexora logo"
    >
      <rect width="12" height="83" fill="#171514" />
      <rect x="580" y="37" width="12" height="46" fill="#171514" />
      <path d="M635 48H647.973L675 83H662.027L635 48Z" fill="#171514" />
      <path d="M755 0H766.838L810 82H798L755 0Z" fill="#93C998" />
      <path d="M767 0H755.162L712 82H724L767 0Z" fill="#93C998" />
      <rect x="88" width="11" height="83" fill="#D9D9D9" />
      <rect x="88" width="12" height="83" fill="#171514" />
      <path d="M147 12V0L245 0L235 12L147 12Z" fill="#171514" />
      <path d="M147 83V71L245 71L235 83L147 83Z" fill="#171514" />
      <path d="M147 48V36L245 36L235 48L147 48Z" fill="#93C998" />
      <path d="M12 17V0L88 66V83L12 17Z" fill="#171514" />
      <path d="M391 0H375L292 83H309L391 0Z" fill="#171514" />
      <path d="M292 0H308L391 83H374L292 0Z" fill="#171514" />
      <rect x="433" y="6" width="94" height="71" rx="20" stroke="#171514" strokeWidth="12" />
      <path d="M580 6H650.5C660.717 6 669 14.2827 669 24.5C669 34.7173 660.717 43 650.5 43H580" stroke="#171514" strokeWidth="12" />
      <path d="M761 33L786 82H736L761 33Z" fill="#171514" />
      <path d="M341.5 21.5L320 0H363L341.5 21.5Z" fill="#93C998" />
    </svg>
  );
}
