import axios from 'axios';

export interface ApiKey {
  id: string;
  dataset_id: string;
  api_key_preview?: string;
  created_at: string;
  active: boolean;
}

export interface AuditLogEntry {
  timestamp: string;
  admin_email: string;
  action: string;
  resource_id?: string;
  details?: string;
}

export interface DatasetRecord {
  dataset_id: string;
  filename: string;
  archived?: boolean;
  status: string;
  trained_model_count: number;
  last_trained_model?: string;
  health_score: number;
  updated_at?: string;
  created_at: string;
}

export interface SystemHealthData {
  status: string;
  services?: {
    api?: string;
    database?: string;
    frontend?: string;
    ollama?: string;
  };
  system?: {
    cpu_percent?: number;
    memory_percent?: number;
    uptime_seconds?: number;
  };
  uptime_seconds?: number;
  memory_usage?: {
    used?: number;
    total?: number;
  };
}

const adminClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  withCredentials: true, // Send cookies with requests
  timeout: 30000,
});

export const adminApi = {
  login: async (email: string, password: string) => {
    const response = await adminClient.post('/admin/login', { email, password });
    return response.data;
  },
  logout: async () => {
    const response = await adminClient.post('/admin/logout');
    return response.data;
  },
  getMe: async () => {
    const response = await adminClient.get('/admin/me');
    return response.data;
  },
  listApiKeys: async () => {
    const response = await adminClient.get('/admin/api-keys');
    return response.data;
  },
  revokeApiKey: async (datasetId: string, deploymentId: string) => {
    const response = await adminClient.post(`/admin/api-keys/${datasetId}/${deploymentId}/revoke`);
    return response.data;
  },
  listDatasets: async () => {
    const response = await adminClient.get('/admin/datasets');
    return response.data;
  },
  deleteDataset: async (datasetId: string) => {
    const response = await adminClient.delete(`/admin/datasets/${datasetId}`);
    return response.data;
  },
  getContent: async (key: string) => {
    const response = await adminClient.get(`/admin/content/${key}`);
    return response.data;
  },
  updateContent: async (key: string, value: unknown, notifyUsers = false) => {
    const response = await adminClient.put(`/admin/content/${key}`, { value, notify_users: notifyUsers });
    return response.data;
  },
  getSystemHealth: async (): Promise<SystemHealthData> => {
    const response = await adminClient.get('/admin/health');
    return response.data;
  },
  getDriftAlerts: async () => {
    const response = await adminClient.get('/admin/drift');
    return response.data;
  },
  getAuditLog: async (limit: number = 100) => {
    const response = await adminClient.get(`/admin/audit?limit=${limit}`);
    return response.data;
  },
  listUsers: async () => {
    const response = await adminClient.get('/admin/users');
    return response.data;
  },
  getUserGrowthStats: async () => {
    const response = await adminClient.get('/admin/users/stats/growth');
    return response.data;
  },
  updateProfile: async (data: { name?: string; avatar_url?: string }) => {
    const response = await adminClient.put('/admin/me', data);
    return response.data;
  },
  resolveDriftAlert: async (datasetId: string, batchId: string, feature: string) => {
    const response = await adminClient.post('/admin/drift/resolve', {
      dataset_id: datasetId,
      batch_id: batchId,
      feature,
    });
    return response.data;
  },
};
