import axios from 'axios';
import { auth } from '../config/firebase';

const communityClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

communityClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export type FeedbackCategory = 'bug' | 'feature' | 'dataset' | 'research' | 'ui' | 'performance' | 'other';
export type FeedbackPriority = 'low' | 'normal' | 'high' | 'urgent';
export type FeedbackStatus = 'waiting' | 'under_review' | 'planned' | 'implemented' | 'closed' | 'duplicate';

export interface CommunityBadge {
  name: string;
  reason: string;
}

export interface FeedbackAttachment {
  name: string;
  url?: string | null;
  kind?: string;
}

export interface FeedbackReply {
  id: string;
  admin_email?: string;
  message: string;
  created_at: string;
}

export interface FeedbackItem {
  id: string;
  user_id: string;
  user_email?: string | null;
  user_name?: string | null;
  title: string;
  category: FeedbackCategory;
  description: string;
  priority: FeedbackPriority;
  suggestion?: string | null;
  attachments?: FeedbackAttachment[];
  status: FeedbackStatus;
  stars: number;
  pinned?: boolean;
  duplicate_of?: string | null;
  badge_awarded?: string | null;
  reactions?: Record<string, string[]>;
  admin_replies?: FeedbackReply[];
  assigned_to?: string | null;
  internal_note?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReputationSummary {
  contribution_score: number;
  feedback_submitted: number;
  feedback_accepted: number;
  features_suggested: number;
  bugs_reported: number;
  replies_received: number;
  badges_earned: number;
  administrator_stars: number;
  implemented_suggestions: number;
  level: string;
  badges: CommunityBadge[];
  recent_feedback: FeedbackItem[];
}

export interface LeaderboardEntry extends ReputationSummary {
  user_id: string;
  name: string;
  email?: string | null;
}

export interface CommunityNotification {
  id: string;
  title: string;
  message: string;
  kind: string;
  feedback_id?: string | null;
  read: boolean;
  created_at: string;
}

export interface FeedbackAnalytics {
  submitted: number;
  open: number;
  closed: number;
  implemented: number;
  average_response_time_hours: number;
  most_requested_features: Array<{ category: string; count: number }>;
  trending_research_topics: Array<{ topic: string; count: number }>;
  top_contributors: LeaderboardEntry[];
  most_active_users: LeaderboardEntry[];
}

export const statusLabels: Record<FeedbackStatus, string> = {
  waiting: 'Waiting',
  under_review: 'Under Review',
  planned: 'Planned',
  implemented: 'Implemented',
  closed: 'Closed',
  duplicate: 'Duplicate',
};

export const categoryLabels: Record<FeedbackCategory, string> = {
  bug: 'Bug',
  feature: 'Feature Request',
  dataset: 'Dataset',
  research: 'Research',
  ui: 'UI',
  performance: 'Performance',
  other: 'Other',
};

export const communityApi = {
  submitFeedback: async (payload: {
    title: string;
    category: FeedbackCategory;
    description: string;
    priority: FeedbackPriority;
    suggestion?: string;
    attachments?: FeedbackAttachment[];
  }): Promise<FeedbackItem> => {
    const { data } = await communityClient.post('/community/feedback', payload);
    return data;
  },
  uploadFiles: async (files: File[]): Promise<{ attachments: FeedbackAttachment[] }> => {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    const { data } = await communityClient.post('/community/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return data;
  },
  getMyFeedback: async (): Promise<FeedbackItem[]> => {
    const { data } = await communityClient.get('/community/feedback/me');
    return data;
  },
  getReputation: async (userId: string): Promise<ReputationSummary> => {
    const { data } = await communityClient.get(`/community/profile/${userId}/reputation`);
    return data;
  },
  getLeaderboard: async (period = 'all'): Promise<LeaderboardEntry[]> => {
    const { data } = await communityClient.get('/community/leaderboard', { params: { period } });
    return data;
  },
  getNotifications: async (): Promise<CommunityNotification[]> => {
    const { data } = await communityClient.get('/community/notifications');
    return data;
  },
  react: async (feedbackId: string, reaction: string): Promise<FeedbackItem> => {
    const { data } = await communityClient.post(`/community/feedback/${feedbackId}/reactions`, { reaction });
    return data;
  },
  getHeatmap: async (userId: string): Promise<{ date: string; count: number }[]> => {
    const { data } = await communityClient.get(`/community/profile/${userId}/heatmap`);
    return data;
  },
  markNotificationsRead: async (): Promise<{ success: boolean }> => {
    const { data } = await communityClient.post('/community/notifications/read');
    return data;
  },
  getPublicFeedback: async (query = '', category = '', status = ''): Promise<FeedbackItem[]> => {
    const { data } = await communityClient.get('/community/feedback/public', { params: { query, category, status } });
    return data;
  },
  getShowcase: async (userId: string): Promise<Record<string, unknown>> => {
    const { data } = await communityClient.get(`/community/profile/${userId}/showcase`);
    return data;
  },
  updateShowcase: async (userId: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> => {
    const { data } = await communityClient.post(`/community/profile/${userId}/showcase`, payload);
    return data;
  },
};

export const adminFeedbackApi = {
  list: async (): Promise<FeedbackItem[]> => {
    const { data } = await communityClient.get('/admin/feedback', { withCredentials: true });
    return data;
  },
  analytics: async (): Promise<FeedbackAnalytics> => {
    const { data } = await communityClient.get('/admin/feedback/analytics', { withCredentials: true });
    return data;
  },
  update: async (feedbackId: string, payload: Partial<Pick<FeedbackItem, 'status' | 'priority' | 'pinned' | 'duplicate_of' | 'stars' | 'badge_awarded'> & { internal_note?: string; assigned_to?: string }>): Promise<FeedbackItem> => {
    const { data } = await communityClient.patch(`/admin/feedback/${feedbackId}`, payload, { withCredentials: true });
    return data;
  },
  reply: async (feedbackId: string, message: string): Promise<FeedbackItem> => {
    const { data } = await communityClient.post(`/admin/feedback/${feedbackId}/replies`, { message }, { withCredentials: true });
    return data;
  },
};
