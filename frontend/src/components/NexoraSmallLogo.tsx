interface Props {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'hero';
}

const VIEWBOX = '0 0 1000 837';
const SVG_SIZES = {
  sm: 32,
  md: 48,
  lg: 120,
  hero: 200,
};

export default function NexoraSmallLogo({ className = '', size = 'md' }: Props) {
  const width = SVG_SIZES[size];
  const height = (width * 837) / 1000;

  return (
    <svg
      width={width}
      height={height}
      viewBox={VIEWBOX}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Nexora small logo"
    >
      <path d="M438.776 0H559.57L1000 836.735H877.551L438.776 0Z" fill="#93C998"/>
      <path d="M561.224 0H440.43L2.09808e-05 836.735H122.449L561.224 0Z" fill="#93C998"/>
      <path d="M500 336.735L755.102 836.735H244.898L500 336.735Z" fill="#171514"/>
    </svg>
  );
}
