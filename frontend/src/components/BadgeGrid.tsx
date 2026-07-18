import React from 'react';

interface Badge {
  name: string;
  reason: string;
}

interface BadgeGridProps {
  badges: Badge[];
}

/**
 * Premium styled badge grid.
 * Displays earned badges in a responsive grid.
 * Hover tooltip shows the badge reason.
 */
const BadgeGrid: React.FC<BadgeGridProps> = ({ badges }) => {
  if (!badges || badges.length === 0) {
    return (
      <span className="text-sm text-gray-400">
        Badges appear here as admins recognize your contributions.
      </span>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
      {badges.map((badge) => (
        <span
          key={badge.name}
          title={badge.reason}
          className="px-3 py-1.5 rounded-full border border-nexora-accent/20 bg-nexora-accent/10 text-nexora-accent text-sm font-medium"
        >
          {badge.name}
        </span>
      ))}
    </div>
  );
};

export default BadgeGrid;
