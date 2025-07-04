// API Configuration
const config = {
  // Determine if we're in development or production
  isDevelopment: process.env.NODE_ENV === 'development',
  
  // API Base URL - use relative path in production, localhost in development
  get apiBaseUrl() {
    if (this.isDevelopment) {
      return 'http://localhost:8001';
    }
    // In production, use relative URLs since frontend and backend are served from same domain
    return '';
  },
  
  // Full API URL for making requests
  get apiUrl() {
    return `${this.apiBaseUrl}/api`;
  }
};

export default config;