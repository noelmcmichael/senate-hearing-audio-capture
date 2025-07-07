const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Comprehensive Senate Hearing Transcription System Test Suite
 * 
 * This test suite implements the QA strategy defined in PLAYWRIGHT_TESTING_PLAN.md
 * focusing on breaking the broken loop problem with comprehensive coverage.
 */

class SenatePlaysrightTester {
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
    this.outputDir = 'playwright-results';
  }

  async init() {
    // Create output directory
    if (fs.existsSync(this.outputDir)) {
      fs.rmSync(this.outputDir, { recursive: true, force: true });
    }
    fs.mkdirSync(this.outputDir, { recursive: true });

    // Launch browser
    this.browser = await chromium.launch({ headless: false });
    this.context = await this.browser.newContext({
      recordVideo: { dir: this.outputDir },
      viewport: { width: 1920, height: 1080 }
    });
    this.page = await this.context.newPage();

    // Set up console logging
    this.page.on('console', msg => {
      console.log(`[${msg.type()}] ${msg.text()}`);
    });

    // Set up error logging
    this.page.on('pageerror', error => {
      console.error(`[PAGE ERROR] ${error.message}`);
    });
  }

  async runTest(testName, testFunction) {
    console.log(`\n🧪 Running test: ${testName}`);
    const testStart = Date.now();
    const testResult = {
      name: testName,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      duration: 0,
      errors: [],
      warnings: [],
      screenshots: [],
      consoleMessages: []
    };

    try {
      // Create test-specific directory
      const testDir = path.join(this.outputDir, testName.replace(/\s+/g, '_').toLowerCase());
      fs.mkdirSync(testDir, { recursive: true });

      // Run the test
      await testFunction(testDir);

      // Take screenshot after test
      const screenshotPath = path.join(testDir, 'final_screenshot.png');
      await this.page.screenshot({ path: screenshotPath, fullPage: true });
      testResult.screenshots.push(screenshotPath);

      testResult.status = 'passed';
      this.results.summary.passed++;
      console.log(`✅ Test passed: ${testName}`);
    } catch (error) {
      testResult.status = 'failed';
      testResult.errors.push({
        message: error.message,
        stack: error.stack
      });
      this.results.summary.failed++;
      console.error(`❌ Test failed: ${testName} - ${error.message}`);

      // Take error screenshot
      const errorScreenshotPath = path.join(this.outputDir, `error_${testName.replace(/\s+/g, '_').toLowerCase()}.png`);
      await this.page.screenshot({ path: errorScreenshotPath, fullPage: true });
      testResult.screenshots.push(errorScreenshotPath);
    }

    testResult.endTime = new Date().toISOString();
    testResult.duration = Date.now() - testStart;
    this.results.tests.push(testResult);
    this.results.summary.totalTests++;
  }

  async testDashboardLoad(testDir) {
    await this.page.goto('http://localhost:3000');
    await this.page.waitForSelector('body', { timeout: 10000 });
    
    // Wait for content to load
    await this.page.waitForTimeout(2000);
    
    // Check for React errors
    const reactErrors = await this.page.evaluate(() => {
      const errors = [];
      if (window.console && window.console.error) {
        // Check for React error messages in console
        const consoleMessages = window.console.error.toString();
        if (consoleMessages.includes('Warning') || consoleMessages.includes('Error')) {
          errors.push('React warnings or errors detected');
        }
      }
      return errors;
    });

    if (reactErrors.length > 0) {
      throw new Error(`React errors detected: ${reactErrors.join(', ')}`);
    }

    // Check for essential elements
    const essentialElements = [
      'body',
      '[data-testid="dashboard"]', // assuming data-testid is used
      'h1, h2, h3' // some heading should be present
    ];

    for (const selector of essentialElements) {
      try {
        await this.page.waitForSelector(selector, { timeout: 5000 });
      } catch (error) {
        console.warn(`⚠️ Element not found: ${selector}`);
        this.results.summary.warnings++;
      }
    }

    await this.page.screenshot({ path: path.join(testDir, 'dashboard_loaded.png'), fullPage: true });
  }

  async testHearingTranscriptNavigation(testDir) {
    await this.page.goto('http://localhost:3000/hearings/12/transcript');
    await this.page.waitForSelector('body', { timeout: 10000 });
    
    // Wait for content to load
    await this.page.waitForTimeout(3000);
    
    // Check for transcript content
    const transcriptContent = await this.page.evaluate(() => {
      const body = document.body.innerText;
      return {
        hasTranscriptData: body.includes('transcript') || body.includes('segments'),
        hasErrorMessage: body.includes('Error') || body.includes('error'),
        hasLoadingState: body.includes('Loading') || body.includes('loading'),
        bodyLength: body.length
      };
    });

    console.log('📊 Transcript page analysis:', transcriptContent);

    if (transcriptContent.hasErrorMessage) {
      throw new Error('Error message detected on transcript page');
    }

    if (transcriptContent.bodyLength < 100) {
      throw new Error('Page content appears to be too short, possible loading issue');
    }

    await this.page.screenshot({ path: path.join(testDir, 'transcript_page.png'), fullPage: true });
  }

  async testApiConnectivity(testDir) {
    // Test API endpoints through browser
    const endpoints = [
      'http://localhost:8001/api/health',
      'http://localhost:8001/api/hearings',
      'http://localhost:8001/api/hearings/12'
    ];

    for (const endpoint of endpoints) {
      await this.page.goto(endpoint);
      await this.page.waitForTimeout(1000);
      
      const responseText = await this.page.evaluate(() => document.body.innerText);
      
      if (responseText.includes('error') || responseText.includes('404') || responseText.includes('500')) {
        throw new Error(`API endpoint ${endpoint} returned error: ${responseText.substring(0, 200)}`);
      }
      
      console.log(`✅ API endpoint working: ${endpoint}`);
    }

    await this.page.screenshot({ path: path.join(testDir, 'api_health.png'), fullPage: true });
  }

  async testTranscriptionWorkflow(testDir) {
    // Navigate to hearing page
    await this.page.goto('http://localhost:3000/hearings/12');
    await this.page.waitForSelector('body', { timeout: 10000 });
    await this.page.waitForTimeout(2000);
    
    // Take screenshot of hearing page
    await this.page.screenshot({ path: path.join(testDir, 'hearing_page.png'), fullPage: true });
    
    // Look for transcription-related buttons
    const buttons = await this.page.evaluate(() => {
      const allButtons = Array.from(document.querySelectorAll('button'));
      return allButtons.map(btn => ({
        text: btn.innerText,
        disabled: btn.disabled,
        className: btn.className
      }));
    });

    console.log('🔘 Buttons found:', buttons);

    // Look for transcription or processing buttons
    const transcriptionButtons = buttons.filter(btn => 
      btn.text.toLowerCase().includes('transcript') || 
      btn.text.toLowerCase().includes('transcribe') ||
      btn.text.toLowerCase().includes('process')
    );

    if (transcriptionButtons.length === 0) {
      console.warn('⚠️ No transcription buttons found');
      this.results.summary.warnings++;
    }

    await this.page.screenshot({ path: path.join(testDir, 'transcription_workflow.png'), fullPage: true });
  }

  async testPerformanceMetrics(testDir) {
    // Test performance metrics
    const performanceMetrics = await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      return {
        loadTime: navigation.loadEventEnd - navigation.loadEventStart,
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        totalTime: navigation.loadEventEnd - navigation.fetchStart
      };
    });

    console.log('⚡ Performance metrics:', performanceMetrics);

    // Alert if performance is poor
    if (performanceMetrics.totalTime > 10000) {
      throw new Error(`Page load time too slow: ${performanceMetrics.totalTime}ms`);
    }

    // Create performance report
    const performanceReport = {
      timestamp: new Date().toISOString(),
      metrics: performanceMetrics,
      thresholds: {
        loadTime: { value: performanceMetrics.loadTime, threshold: 5000, status: performanceMetrics.loadTime < 5000 ? 'pass' : 'warn' },
        totalTime: { value: performanceMetrics.totalTime, threshold: 10000, status: performanceMetrics.totalTime < 10000 ? 'pass' : 'fail' }
      }
    };

    fs.writeFileSync(path.join(testDir, 'performance_report.json'), JSON.stringify(performanceReport, null, 2));
  }

  async testErrorScenarios(testDir) {
    // Test various error scenarios
    const errorScenarios = [
      { url: 'http://localhost:3000/hearings/999999', name: 'invalid_hearing_id' },
      { url: 'http://localhost:3000/nonexistent-page', name: 'nonexistent_page' }
    ];

    for (const scenario of errorScenarios) {
      await this.page.goto(scenario.url);
      await this.page.waitForTimeout(2000);
      
      const pageContent = await this.page.evaluate(() => document.body.innerText);
      
      // Check if error is handled gracefully
      const hasGracefulError = pageContent.includes('Not Found') || 
                              pageContent.includes('404') || 
                              pageContent.includes('Page not found') ||
                              pageContent.includes('Error');

      if (!hasGracefulError) {
        console.warn(`⚠️ Error scenario '${scenario.name}' may not be handled gracefully`);
        this.results.summary.warnings++;
      }

      await this.page.screenshot({ path: path.join(testDir, `error_${scenario.name}.png`), fullPage: true });
    }
  }

  async generateReport() {
    this.results.summary.endTime = new Date().toISOString();
    
    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>Senate Hearing Transcription System - Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
        .test { border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .passed { border-left: 5px solid #28a745; }
        .failed { border-left: 5px solid #dc3545; }
        .warning { color: #856404; }
        .error { color: #721c24; }
        .screenshot { max-width: 300px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>Senate Hearing Transcription System - Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tests:</strong> ${this.results.summary.totalTests}</p>
        <p><strong>Passed:</strong> ${this.results.summary.passed}</p>
        <p><strong>Failed:</strong> ${this.results.summary.failed}</p>
        <p><strong>Warnings:</strong> ${this.results.summary.warnings}</p>
        <p><strong>Start Time:</strong> ${this.results.summary.startTime}</p>
        <p><strong>End Time:</strong> ${this.results.summary.endTime}</p>
    </div>
    
    <h2>Test Results</h2>
    ${this.results.tests.map(test => `
        <div class="test ${test.status}">
            <h3>${test.name}</h3>
            <p><strong>Status:</strong> ${test.status}</p>
            <p><strong>Duration:</strong> ${test.duration}ms</p>
            ${test.errors.length > 0 ? `<div class="error">Errors: ${test.errors.map(e => e.message).join(', ')}</div>` : ''}
            ${test.warnings.length > 0 ? `<div class="warning">Warnings: ${test.warnings.join(', ')}</div>` : ''}
            ${test.screenshots.map(screenshot => `<img src="${screenshot}" class="screenshot" alt="Screenshot">`).join('')}
        </div>
    `).join('')}
</body>
</html>
    `;

    fs.writeFileSync(path.join(this.outputDir, 'test_report.html'), htmlReport);
    fs.writeFileSync(path.join(this.outputDir, 'test_results.json'), JSON.stringify(this.results, null, 2));
  }

  async runAllTests() {
    console.log('🚀 Starting comprehensive Senate Hearing Transcription System tests...');
    
    await this.init();

    // Core test suite
    await this.runTest('Dashboard Load', this.testDashboardLoad.bind(this));
    await this.runTest('Hearing Transcript Navigation', this.testHearingTranscriptNavigation.bind(this));
    await this.runTest('API Connectivity', this.testApiConnectivity.bind(this));
    await this.runTest('Transcription Workflow', this.testTranscriptionWorkflow.bind(this));
    await this.runTest('Performance Metrics', this.testPerformanceMetrics.bind(this));
    await this.runTest('Error Scenarios', this.testErrorScenarios.bind(this));

    await this.generateReport();

    // Clean up
    await this.context.close();
    await this.browser.close();

    console.log('\n📊 Test Results Summary:');
    console.log(`Total Tests: ${this.results.summary.totalTests}`);
    console.log(`Passed: ${this.results.summary.passed}`);
    console.log(`Failed: ${this.results.summary.failed}`);
    console.log(`Warnings: ${this.results.summary.warnings}`);
    console.log(`\n📁 Results saved to: ${this.outputDir}/`);
    console.log(`📄 HTML Report: ${this.outputDir}/test_report.html`);

    return this.results.summary.failed === 0;
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new SenatePlaysrightTester();
  tester.runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  }).catch(error => {
    console.error('Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = SenatePlaysrightTester;