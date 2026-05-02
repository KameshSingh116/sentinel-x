// ─── Sentinel-X Mobile Configuration ─────────────────────────────────────────
// Update BASE_URL to point to your Sentinel-X backend.
// For local dev: http://YOUR_LOCAL_IP:5000
// For production: https://your-deployment-url.replit.app

const BASE_URL = "http://YOUR_BACKEND_IP:5000";

export const API_BASE = BASE_URL;

export const ENDPOINTS = {
  health:       `${BASE_URL}/api/health`,
  status:       `${BASE_URL}/api/status`,
  alerts:       `${BASE_URL}/api/alerts`,
  logs:         `${BASE_URL}/api/logs`,
  processes:    `${BASE_URL}/api/processes`,
  anomalies:    `${BASE_URL}/api/anomalies`,
  triggerTest:  `${BASE_URL}/api/trigger-test-alert`,
};

export const REFRESH_INTERVAL_MS = 30000;
