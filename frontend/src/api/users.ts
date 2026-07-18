import axios from 'axios';
import { auth } from '../config/firebase';

const userClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
});

userClient.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface UserProfile {
  user_id: string;
  email?: string | null;
  name?: string;
  username?: string;
  bio?: string;
  avatar_url?: string;
  role: string;
  is_public: boolean;
  requires_2fa: boolean;
  auth_providers?: string[];
  last_login?: string;
  login_history?: Array<{ at: string; method: string; user_agent?: string; ip?: string }>;
  links?: Record<string, { url: string; is_visible: boolean; verified?: boolean }>;
  created_at: string;
}

export function fallbackProfileFromFirebaseUser(): UserProfile | null {
  const user = auth.currentUser;
  if (!user) return null;
  return {
    user_id: user.uid,
    email: user.email,
    name: user.displayName || 'Nexora User',
    avatar_url: user.photoURL || undefined,
    role: 'user',
    is_public: true,
    requires_2fa: false,
    created_at: new Date().toISOString(),
  };
}
export interface UserProfileUpdate {
  name?: string;
  username?: string;
  bio?: string;
  avatar_url?: string;
  is_public?: boolean;
  requires_2fa?: boolean;
  links?: Record<string, { url: string; is_visible: boolean }>;
}

export const userApi = {
  getMe: async (): Promise<UserProfile> => {
    const { data } = await userClient.get('/users/me');
    return data;
  },
  updateMe: async (update: UserProfileUpdate): Promise<UserProfile> => {
    try {
      const { data } = await userClient.put('/users/me', update);
      return data;
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        const detail = error.response?.data?.detail || error.response?.data?.message;
        throw new Error(detail || error.message);
      }
      throw error;
    }
  },
  getPublicProfile: async (username: string): Promise<UserProfile> => {
    const { data } = await userClient.get(`/users/profile/${username}`);
    return data;
  },
  getMyDatasets: async () => {
    const { data } = await userClient.get('/users/me/datasets');
    return data.datasets ?? [];
  },
  exportData: async () => {
    const { data } = await userClient.get('/users/me/export');
    return data;
  },
  deleteAccount: async () => {
    const { data } = await userClient.delete('/users/me');
    return data;
  },
  getActivity: async () => {
    const { data } = await userClient.get('/users/me/activity');
    return data;
  },
  revokeAllSessions: async () => {
    const { data } = await userClient.post('/users/me/sessions/revoke-all');
    return data;
  },
  notifyPasswordChanged: async () => {
    const { data } = await userClient.post('/users/me/notify/password-changed');
    return data;
  },
  notifyNewLogin: async () => {
    const { data } = await userClient.post('/users/me/notify/new-login');
    return data;
  },
};

export async function getPublicContent(key: string) {
  const base = import.meta.env.VITE_API_BASE_URL || '/api';
  const { data } = await axios.get(`${base}/content/${key}`);
  return data;
}
