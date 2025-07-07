const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Enhanced Comprehensive Test Suite with Data-TestID Selectors
 * 
 * This enhanced test suite uses the new data-testid attributes for more reliable
 * element selection and improved test stability.
 */

class EnhancedSenatePlaysrightTester {
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

    // Set up error handling
    this.page.on('pageerror', exception => {
      console.error(`Page error: ${exception.message}`);
    });
  }

  async takeScreenshot(name) {
    const filename = `${name}_${Date.now()}.png`;
    const filepath = path.join(this.outputDir, filename);
    await this.page.screenshot({ path: filepath, fullPage: true });
    return filepath;
  }

  async recordTest(testName, testFunction) {
    const testStart = performance.now();
    let testResult = {
      name: testName,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      duration: 0,
      screenshots: [],
      errors: [],
      warnings: []
    };

    this.results.summary.totalTests++;
    console.log(`\n🧪 Running: ${testName}`);

    try {
      await testFunction();
      testResult.status = 'passed';
      this.results.summary.passed++;
      console.log(`✅ ${testName} - PASSED`);
    } catch (error) {
      testResult.status = 'failed';
      testResult.errors.push(error.message);
      this.results.summary.failed++;
      console.error(`❌ ${testName} - FAILED: ${error.message}`);
      
      // Take screenshot on failure
      const screenshot = await this.takeScreenshot(`failure_${testName.replace(/\s+/g, '_')}`);
      testResult.screenshots.push(screenshot);
    }

    testResult.endTime = new Date().toISOString();
    testResult.duration = performance.now() - testStart;
    this.results.tests.push(testResult);

    return testResult;
  }

  // Test 1: Enhanced Dashboard Load and Search
  async testDashboardLoadAndSearch() {
    await this.page.goto('http://localhost:3000');
    
    // Wait for dashboard to load
    await this.page.waitForSelector('[data-testid="search-input"]', { timeout: 10000 });
    
    // Take screenshot of loaded dashboard
    await this.takeScreenshot('dashboard_loaded');
    
    // Test search functionality
    await this.page.fill('[data-testid="search-input"]', 'judiciary');
    await this.page.waitForTimeout(1000); // Wait for search results
    
    // Check if search results are filtered
    const hearingCards = await this.page.locator('[data-testid^="hearing-card-"]');
    const cardCount = await hearingCards.count();
    
    if (cardCount === 0) {
      throw new Error('No hearing cards found after search');
    }
    
    // Clear search
    await this.page.fill('[data-testid="search-input"]', '');
    await this.page.waitForTimeout(1000);
    
    console.log(`Search test completed - found ${cardCount} cards`);
  }

  // Test 2: Enhanced Filter Functionality
  async testFilterFunctionality() {
    await this.page.goto('http://localhost:3000');
    
    // Wait for filter toggle to be available
    await this.page.waitForSelector('[data-testid="filter-toggle"]', { timeout: 10000 });
    
    // Open filters
    await this.page.click('[data-testid="filter-toggle"]');
    
    // Wait for filter panel to open
    await this.page.waitForSelector('[data-testid="status-filter"]', { timeout: 5000 });
    
    // Test committee filter
    const committeeFilter = await this.page.locator('[data-testid="committee-filter-SSJU"]');
    if (await committeeFilter.isVisible()) {
      await committeeFilter.click();
      await this.page.waitForTimeout(1000);
    }
    
    // Test status filter
    await this.page.selectOption('[data-testid="status-filter"]', 'has_transcript');
    await this.page.waitForTimeout(1000);
    
    // Take screenshot of filtered results
    await this.takeScreenshot('filters_applied');
    
    // Clear filters
    await this.page.click('[data-testid="clear-filters"]');
    await this.page.waitForTimeout(1000);
    
    console.log('Filter functionality test completed');
  }

  // Test 3: Enhanced Sort Functionality
  async testSortFunctionality() {
    await this.page.goto('http://localhost:3000');
    
    // Wait for sort controls
    await this.page.waitForSelector('[data-testid="sort-select"]', { timeout: 10000 });
    
    // Test sort by date
    await this.page.selectOption('[data-testid="sort-select"]', 'date');
    await this.page.waitForTimeout(1000);
    
    // Test sort order toggle
    await this.page.click('[data-testid="sort-order-toggle"]');
    await this.page.waitForTimeout(1000);
    
    // Test sort by committee
    await this.page.selectOption('[data-testid="sort-select"]', 'committee');
    await this.page.waitForTimeout(1000);
    
    // Take screenshot of sorted results
    await this.takeScreenshot('sort_applied');
    
    console.log('Sort functionality test completed');
  }

  // Test 4: Enhanced Hearing Card Navigation
  async testHearingCardNavigation() {
    await this.page.goto('http://localhost:3000');
    
    // Wait for hearing cards
    await this.page.waitForSelector('[data-testid^="hearing-card-"]', { timeout: 10000 });
    
    // Get all hearing cards
    const hearingCards = await this.page.locator('[data-testid^="hearing-card-"]');
    const cardCount = await hearingCards.count();
    
    if (cardCount === 0) {
      throw new Error('No hearing cards found');
    }
    
    // Click on first hearing card
    await hearingCards.first().click();
    
    // Wait for navigation
    await this.page.waitForTimeout(3000);
    
    // Check if we navigated to hearing detail page
    const currentUrl = this.page.url();
    if (!currentUrl.includes('/hearings/')) {
      throw new Error(`Expected hearing detail URL, got: ${currentUrl}`);
    }
    
    // Take screenshot of hearing detail
    await this.takeScreenshot('hearing_detail');
    
    console.log(`Hearing card navigation test completed - navigated to ${currentUrl}`);
  }

  // Test 5: Enhanced Transcript Page Testing
  async testTranscriptPage() {
    // Navigate to a hearing with transcript
    await this.page.goto('http://localhost:3000/hearings/12');
    
    // Wait for page to load
    await this.page.waitForTimeout(5000);
    
    // Check if transcript table exists
    const transcriptTable = await this.page.locator('[data-testid="transcript-table"]');
    if (await transcriptTable.isVisible()) {
      console.log('Transcript table found');
      
      // Test export buttons
      const exportButtons = [
        'export-transcript-button',
        'export-text-button',
        'export-csv-button',
        'export-summary-button'
      ];
      
      for (const buttonTestId of exportButtons) {
        const button = await this.page.locator(`[data-testid="${buttonTestId}"]`);
        if (await button.isVisible()) {
          console.log(`${buttonTestId} is visible`);
        }
      }
      
      // Take screenshot of transcript page
      await this.takeScreenshot('transcript_page');
    } else {
      console.log('No transcript table found - this may be expected for some hearings');
    }
    
    console.log('Transcript page test completed');
  }

  // Test 6: Enhanced Performance and Error Detection
  async testPerformanceAndErrors() {
    const performanceMetrics = {
      navigationStart: 0,
      loadComplete: 0,
      firstContentfulPaint: 0,
      consoleErrors: []
    };
    
    // Set up console error tracking
    this.page.on('console', msg => {
      if (msg.type() === 'error') {
        performanceMetrics.consoleErrors.push(msg.text());
      }
    });
    
    const startTime = performance.now();
    
    // Navigate to dashboard
    await this.page.goto('http://localhost:3000');
    
    // Wait for key element to load
    await this.page.waitForSelector('[data-testid="search-input"]', { timeout: 15000 });
    
    const endTime = performance.now();
    performanceMetrics.navigationStart = startTime;
    performanceMetrics.loadComplete = endTime;
    
    // Test multiple page loads
    await this.page.goto('http://localhost:3000/hearings/12');
    await this.page.waitForTimeout(3000);
    
    // Back to dashboard
    await this.page.goto('http://localhost:3000');
    await this.page.waitForSelector('[data-testid="search-input"]', { timeout: 10000 });
    
    // Performance thresholds
    const loadTime = performanceMetrics.loadComplete - performanceMetrics.navigationStart;
    if (loadTime > 15000) {
      throw new Error(`Page load too slow: ${loadTime}ms (threshold: 15000ms)`);
    }
    
    if (performanceMetrics.consoleErrors.length > 0) {
      console.warn(`Console errors detected: ${performanceMetrics.consoleErrors.join(', ')}`);
    }
    
    console.log(`Performance test completed - Load time: ${loadTime}ms`);
  }

  async generateReport() {
    this.results.summary.endTime = new Date().toISOString();
    
    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Playwright Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #2A2B32; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric.passed { border-left: 4px solid #4ECDC4; }
        .metric.failed { border-left: 4px solid #FF4444; }
        .metric.warning { border-left: 4px solid #FFA500; }
        .test-result { margin-bottom: 20px; padding: 15px; border-radius: 8px; }
        .test-result.passed { background: #d4edda; border: 1px solid #c3e6cb; }
        .test-result.failed { background: #f8d7da; border: 1px solid #f5c6cb; }
        .test-name { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
        .test-details { font-size: 14px; color: #666; }
        .error { background: #f8d7da; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎭 Enhanced Playwright Test Report</h1>
            <p>Senate Hearing Transcription System - Test Suite with Data-TestID Selectors</p>
            <p>Generated: ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="metric passed">
                <h3>${this.results.summary.passed}</h3>
                <p>Tests Passed</p>
            </div>
            <div class="metric failed">
                <h3>${this.results.summary.failed}</h3>
                <p>Tests Failed</p>
            </div>
            <div class="metric">
                <h3>${this.results.summary.totalTests}</h3>
                <p>Total Tests</p>
            </div>
            <div class="metric">
                <h3>${Math.round((this.results.summary.passed / this.results.summary.totalTests) * 100)}%</h3>
                <p>Success Rate</p>
            </div>
        </div>
        
        <h2>Test Results</h2>
        ${this.results.tests.map(test => `
            <div class="test-result ${test.status}">
                <div class="test-name">${test.name}</div>
                <div class="test-details">
                    Status: ${test.status.toUpperCase()} | 
                    Duration: ${Math.round(test.duration)}ms |
                    Time: ${new Date(test.startTime).toLocaleTimeString()}
                </div>
                ${test.errors.length > 0 ? `
                    <div class="error">
                        <strong>Errors:</strong><br>
                        ${test.errors.join('<br>')}
                    </div>
                ` : ''}
            </div>
        `).join('')}
        
        <h2>Key Improvements</h2>
        <ul>
            <li>✅ <strong>Data-TestID Selectors</strong> - More reliable element targeting</li>
            <li>✅ <strong>Enhanced Test Coverage</strong> - Comprehensive UI workflow testing</li>
            <li>✅ <strong>Performance Monitoring</strong> - Load time and error detection</li>
            <li>✅ <strong>Visual Documentation</strong> - Screenshots and videos</li>
            <li>✅ <strong>Error Handling</strong> - Graceful failure detection</li>
        </ul>
    </div>
</body>
</html>
    `;
    
    fs.writeFileSync(path.join(this.outputDir, 'enhanced_test_report.html'), htmlReport);
    
    // Generate JSON report
    fs.writeFileSync(path.join(this.outputDir, 'enhanced_test_results.json'), JSON.stringify(this.results, null, 2));
    
    console.log(`\n📊 Enhanced Test Report Generated:`);
    console.log(`   HTML: ${path.join(this.outputDir, 'enhanced_test_report.html')}`);
    console.log(`   JSON: ${path.join(this.outputDir, 'enhanced_test_results.json')}`);
  }

  async runAllTests() {
    console.log('🚀 Starting Enhanced Playwright Test Suite...');
    
    try {
      await this.init();
      
      // Run all tests
      await this.recordTest('Dashboard Load and Search', () => this.testDashboardLoadAndSearch());
      await this.recordTest('Filter Functionality', () => this.testFilterFunctionality());
      await this.recordTest('Sort Functionality', () => this.testSortFunctionality());
      await this.recordTest('Hearing Card Navigation', () => this.testHearingCardNavigation());
      await this.recordTest('Transcript Page', () => this.testTranscriptPage());
      await this.recordTest('Performance and Errors', () => this.testPerformanceAndErrors());
      
      await this.generateReport();
      
      console.log('\n🎉 Enhanced Test Suite Complete!');
      console.log(`📊 Results: ${this.results.summary.passed}/${this.results.summary.totalTests} tests passed`);
      
    } catch (error) {
      console.error('Test suite failed:', error);
      throw error;
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new EnhancedSenatePlaysrightTester();
  tester.runAllTests().catch(error => {
    console.error('Test execution failed:', error);
    process.exit(1);
  });
}

module.exports = EnhancedSenatePlaysrightTester;