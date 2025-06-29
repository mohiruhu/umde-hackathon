export const environment = {
  production: true,
  apiBaseUrl: 'https://api.umde.com', // ✅ Must be HTTPS
 
  features: {
    enablelogging: true,
    auditLogs: true,
    showConfidenceChart: true,
    enableVerboseLogs: false,
    mockData: false, // Use real data in production
  }
};
