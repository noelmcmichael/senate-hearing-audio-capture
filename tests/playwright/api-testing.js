const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * API Testing Suite
 * 
 * Comprehensive testing of backend API endpoints for functionality,
 * response schemas, and error handling.
 */

class APITestSuite {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.results = {
      summary: {
        totalTests: 0,
        passed: 0,
        failed: 0,
        warnings: 0,
        startTime: new Date().toISOString(),
        endTime: null
      },
      tests: []
    };
    this.outputDir = 'playwright-results/api';
    this.baseUrl = 'http://localhost:8001';
  }

  async init() {
    // Create output directory
    if (!fs.existsSync('playwright-results')) {
      fs.mkdirSync('playwright-results', { recursive: true });
    }
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    // Launch browser for API testing (we'll use it for some tests)
    this.browser = await chromium.launch({ headless: true });
    this.context = await this.browser.newContext();
    this.page = await this.context.newPage();

    console.log('🚀 Starting API Testing Suite...');
  }

  async runTest(testName, testFunction) {
    const test = {
      name: testName,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      duration: null,
      errors: [],
      warnings: [],
      response: null
    };

    this.results.summary.totalTests++;
    console.log(`🧪 Testing: ${testName}`);

    const startTime = performance.now();
    
    try {
      const result = await testFunction();
      test.response = result;
      test.status = 'passed';
      this.results.summary.passed++;
      console.log(`✅ ${testName} - PASSED`);
    } catch (error) {
      test.status = 'failed';
      test.errors.push(error.message);
      this.results.summary.failed++;
      console.log(`❌ ${testName} - FAILED: ${error.message}`);
    }

    const endTime = performance.now();
    test.endTime = new Date().toISOString();
    test.duration = endTime - startTime;

    this.results.tests.push(test);
  }

  async testHealthEndpoint() {
    const response = await fetch(`${this.baseUrl}/api/health`);
    
    if (!response.ok) {
      throw new Error(`Health check failed: ${response.status}`);
    }

    const data = await response.json();
    
    // Validate response structure
    if (!data.status) {
      throw new Error('Health response missing status field');
    }

    return {
      status: response.status,
      data: data,
      responseTime: response.headers.get('x-response-time') || 'N/A'
    };
  }

  async testCommitteeHearingsEndpoint() {
    const committees = ['SCOM', 'SSCI', 'SSJU', 'HJUD', 'SBAN'];
    const results = {};

    for (const committee of committees) {
      const response = await fetch(`${this.baseUrl}/api/committees/${committee}/hearings`);
      
      if (!response.ok) {
        throw new Error(`Committee ${committee} hearings failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate response structure
      if (!data.hearings || !Array.isArray(data.hearings)) {
        throw new Error(`Committee ${committee} response missing hearings array`);
      }

      // Validate hearing structure
      if (data.hearings.length > 0) {
        const hearing = data.hearings[0];
        const requiredFields = ['id', 'committee_code', 'hearing_title', 'hearing_date'];
        
        for (const field of requiredFields) {
          if (!(field in hearing)) {
            throw new Error(`Committee ${committee} hearing missing field: ${field}`);
          }
        }
      }

      results[committee] = {
        count: data.hearings.length,
        status: response.status
      };
    }

    return results;
  }

  async testTranscriptBrowserEndpoint() {
    const response = await fetch(`${this.baseUrl}/api/transcript-browser/hearings`);
    
    if (!response.ok) {
      throw new Error(`Transcript browser failed: ${response.status}`);
    }

    const data = await response.json();
    
    // Validate response structure
    if (!data.transcripts || !Array.isArray(data.transcripts)) {
      throw new Error('Transcript browser response missing transcripts array');
    }

    // Validate transcript structure if any exist
    if (data.transcripts.length > 0) {
      const transcript = data.transcripts[0];
      const requiredFields = ['hearing_id', 'segments'];
      
      for (const field of requiredFields) {
        if (!(field in transcript)) {
          throw new Error(`Transcript missing field: ${field}`);
        }
      }
    }

    return {
      count: data.transcripts.length,
      status: response.status
    };
  }

  async testHearingDetailsEndpoint() {
    // Test with a known hearing ID
    const hearingId = 12;
    const response = await fetch(`${this.baseUrl}/api/hearings/${hearingId}`);
    
    if (!response.ok) {
      throw new Error(`Hearing details failed: ${response.status}`);
    }

    const data = await response.json();
    
    // Validate response structure
    const hearing = data.hearing || data;
    if (!hearing || typeof hearing !== 'object') {
      throw new Error('Hearing details response invalid structure');
    }

    // Check for required fields
    const requiredFields = ['id', 'committee_code'];
    for (const field of requiredFields) {
      if (!(field in hearing)) {
        throw new Error(`Hearing details missing field: ${field}`);
      }
    }

    return {
      hearingId: hearing.id,
      committee: hearing.committee_code,
      status: response.status
    };
  }

  async testErrorHandling() {
    const tests = [
      { url: '/api/hearings/99999', expectedStatus: 404, description: 'Non-existent hearing' },
      { url: '/api/committees/INVALID/hearings', expectedStatus: 200, description: 'Invalid committee (should return empty)' },
      { url: '/api/nonexistent', expectedStatus: 404, description: 'Non-existent endpoint' }
    ];

    const results = {};

    for (const test of tests) {
      const response = await fetch(`${this.baseUrl}${test.url}`);
      
      if (test.expectedStatus === 404 && response.status !== 404) {
        throw new Error(`${test.description}: Expected 404, got ${response.status}`);
      }

      results[test.description] = {
        expectedStatus: test.expectedStatus,
        actualStatus: response.status,
        passed: response.status === test.expectedStatus || 
                (test.expectedStatus === 200 && response.status === 200)
      };
    }

    return results;
  }

  async testResponseTimes() {
    const endpoints = [
      '/api/health',
      '/api/committees/SCOM/hearings',
      '/api/transcript-browser/hearings'
    ];

    const results = {};
    const timeoutThreshold = 5000; // 5 seconds

    for (const endpoint of endpoints) {
      const startTime = performance.now();
      const response = await fetch(`${this.baseUrl}${endpoint}`);
      const endTime = performance.now();
      
      const responseTime = endTime - startTime;
      
      if (responseTime > timeoutThreshold) {
        throw new Error(`${endpoint} response time ${responseTime}ms exceeds ${timeoutThreshold}ms threshold`);
      }

      results[endpoint] = {
        responseTime: Math.round(responseTime),
        status: response.status,
        passed: responseTime <= timeoutThreshold
      };
    }

    return results;
  }

  async testDataConsistency() {
    // Get hearings from committee endpoint
    const committeeResponse = await fetch(`${this.baseUrl}/api/committees/SSJU/hearings`);
    const committeeData = await committeeResponse.json();
    
    if (committeeData.hearings.length === 0) {
      throw new Error('No hearings found for consistency test');
    }

    const hearingId = committeeData.hearings[0].id;
    
    // Get same hearing from details endpoint
    const detailsResponse = await fetch(`${this.baseUrl}/api/hearings/${hearingId}`);
    const detailsData = await detailsResponse.json();
    
    const detailsHearing = detailsData.hearing || detailsData;
    const committeeHearing = committeeData.hearings[0];

    // Check consistency
    if (detailsHearing.id !== committeeHearing.id) {
      throw new Error('Hearing ID inconsistency between endpoints');
    }

    if (detailsHearing.committee_code !== committeeHearing.committee_code) {
      throw new Error('Committee code inconsistency between endpoints');
    }

    return {
      hearingId: hearingId,
      consistencyChecks: ['id', 'committee_code'],
      passed: true
    };
  }

  async generateReport() {
    this.results.summary.endTime = new Date().toISOString();
    
    // Calculate success rate
    const successRate = this.results.summary.totalTests > 0 
      ? Math.round((this.results.summary.passed / this.results.summary.totalTests) * 100)
      : 0;

    // Generate JSON report
    const jsonReport = {
      ...this.results,
      successRate: successRate,
      timestamp: new Date().toISOString()
    };

    fs.writeFileSync(
      path.join(this.outputDir, 'api_test_results.json'),
      JSON.stringify(jsonReport, null, 2)
    );

    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>API Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1B1C20; color: #FFFFFF; }
        .header { background: #2A2B32; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .success { color: #4ECDC4; }
        .failure { color: #FF4444; }
        .warning { color: #FFA500; }
        .test-card { background: #2A2B32; border: 1px solid #444; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .response-data { background: #1B1C20; padding: 10px; border-radius: 4px; margin-top: 10px; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔌 API Test Results</h1>
        <div class="metric">Success Rate: <span class="${successRate >= 80 ? 'success' : 'failure'}">${successRate}%</span></div>
        <div class="metric">Total Tests: ${this.results.summary.totalTests}</div>
        <div class="metric">Passed: <span class="success">${this.results.summary.passed}</span></div>
        <div class="metric">Failed: <span class="failure">${this.results.summary.failed}</span></div>
        <div class="metric">Generated: ${new Date().toLocaleString()}</div>
    </div>

    ${this.results.tests.map(test => `
        <div class="test-card">
            <h3>${test.status === 'passed' ? '✅' : '❌'} ${test.name}</h3>
            <div>Status: <span class="${test.status === 'passed' ? 'success' : 'failure'}">${test.status.toUpperCase()}</span></div>
            <div>Duration: ${Math.round(test.duration)}ms</div>
            ${test.errors.length > 0 ? `<div class="failure">Errors: ${test.errors.join(', ')}</div>` : ''}
            ${test.response ? `<div class="response-data">${JSON.stringify(test.response, null, 2)}</div>` : ''}
        </div>
    `).join('')}
</body>
</html>`;

    fs.writeFileSync(path.join(this.outputDir, 'api_test_report.html'), htmlReport);

    console.log(`📊 API Test Report Generated:`);
    console.log(`   HTML: ${this.outputDir}/api_test_report.html`);
    console.log(`   JSON: ${this.outputDir}/api_test_results.json`);
  }

  async runAllTests() {
    await this.init();

    // Run all API tests
    await this.runTest('Health Endpoint', () => this.testHealthEndpoint());
    await this.runTest('Committee Hearings Endpoints', () => this.testCommitteeHearingsEndpoint());
    await this.runTest('Transcript Browser Endpoint', () => this.testTranscriptBrowserEndpoint());
    await this.runTest('Hearing Details Endpoint', () => this.testHearingDetailsEndpoint());
    await this.runTest('Error Handling', () => this.testErrorHandling());
    await this.runTest('Response Times', () => this.testResponseTimes());
    await this.runTest('Data Consistency', () => this.testDataConsistency());

    await this.generateReport();

    const successRate = Math.round((this.results.summary.passed / this.results.summary.totalTests) * 100);
    console.log(`🎉 API Testing Complete!`);
    console.log(`📊 Results: ${this.results.summary.passed}/${this.results.summary.totalTests} tests passed (${successRate}%)`);

    if (this.browser) {
      await this.browser.close();
    }

    return this.results;
  }
}

// Run the test suite
if (require.main === module) {
  const apiTester = new APITestSuite();
  apiTester.runAllTests().catch(console.error);
}

module.exports = APITestSuite;