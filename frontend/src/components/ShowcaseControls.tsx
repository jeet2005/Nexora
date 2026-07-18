import React, { useState, useEffect } from 'react';
import { communityApi } from '../api/community';
import { Check, X } from 'lucide-react';

interface ShowcaseControlsProps {
  userId: string;
}

/**
 * Simple toggle to pin the current dataset/model/feedback as a showcase.
 * Calls the backend endpoint `/api/community/profile/{userId}/showcase` (POST).
 */
const ShowcaseControls: React.FC<ShowcaseControlsProps> = ({ userId }) => {
  const [pinned, setPinned] = useState(false);
  const [loading, setLoading] = useState(false);

  // Load current showcase status on mount (placeholder – using reputation for now)
  useEffect(() => {
    communityApi.getReputation(userId)
      .then((rep) => setPinned(!!(rep as any).showcasePinned))
      .catch(() => setPinned(false));
  }, [userId]);

  const toggleShowcase = async () => {
    if (loading) return;
    setLoading(true);
    try {
      await communityApi.updateShowcase(userId, { pinned: !pinned });
      setPinned(!pinned);
    } catch (e) {
      console.error('Failed to update showcase', e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={toggleShowcase}
      disabled={loading}
      className="btn-outline flex items-center gap-2 px-3 py-1.5 text-sm"
    >
      {pinned ? <Check size={16} className="text-green-600" /> : <X size={16} className="text-gray-600" />}
      {pinned ? 'Pinned as Showcase' : 'Pin as Showcase'}
    </button>
  );
};

export default ShowcaseControls;
