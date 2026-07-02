import axios from 'axios';

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
  updateContent: async (key: string, value: any, notifyUsers = false) => {
    const response = await adminClient.put(`/admin/content/${key}`, { value, notify_users: notifyUsers });
    return response.data;
  },
  getSystemHealth: async () => {
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
