/**
 * Development environment configuration
 * Location: frontend/src/environments/environment.ts
 */

export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8000',  // Update with your backend URL
  
  // Feature flags
  features: {
    mockData: true,          // Use mock data when backend isn't ready
    enableLogging: true,
    verboseLogging: true,    // Enable detailed console.debug logs
    retryFailedRequests: true
  },
  
  // API endpoints (optional - can also hardcode in service)
  api: {
    rules: {
      review: '/api/rules/review',
      approve: '/api/rules/approve',
      reject: '/api/rules/reject',
      commit: '/api/rules/commit',
      triggerEligible: '/api/rules/trigger-eligible',
      run: '/api/rules/run',
      history: '/api/rules/history'
    }
  }
};