const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Performance Monitoring Test Suite
 * 
 * This suite establishes performance baselines and monitors for regressions
 * with automated alerts for load time degradation.
 */

class PerformanceMonitor {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.outputDir = 'playwright-results';
    this.baselineFile = path.join(this.outputDir, 'performance_baseline.json');
    this.historyFile = path.join(this.outputDir, 'performance_history.json');
    
    // Performance thresholds
    this.thresholds = {
      dashboardLoad: 15000,    // 15 seconds max
      hearingPageLoad: 10000,  // 10 seconds max
      searchResponse: 2000,    // 2 seconds max
      filterResponse: 1000,    // 1 second max
      firstContentfulPaint: 3000, // 3 seconds max
      largestContentfulPaint: 4000, // 4 seconds max
      cumulativeLayoutShift: 0.1,  // CLS threshold
      firstInputDelay: 100     // 100ms max
    };
    
    this.results = {
      timestamp: new Date().toISOString(),
      tests: [],
      summary: {
        passed: 0,
        failed: 0,
        warnings: 0,
        totalTests: 0
      },
      alerts: []
    };
  }

  async init() {
    // Ensure output directory exists
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }

    // Launch browser with performance monitoring
    this.browser = await chromium.launch({ 
      headless: false,
      args: ['--enable-web-metrics']
    });
    
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      recordVideo: { dir: this.outputDir }
    });
    
    this.page = await this.context.newPage();
    
    // Enable performance monitoring
    await this.page.addInitScript(() => {
      // Add performance observer
      if ('PerformanceObserver' in window) {
        const observer = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'largest-contentful-paint') {
              window.lcpValue = entry.startTime;
            }
            if (entry.entryType === 'first-input') {
              window.fidValue = entry.processingStart - entry.startTime;
            }
            if (entry.entryType === 'layout-shift') {
              if (!window.clsValue) window.clsValue = 0;
              if (!entry.hadRecentInput) {
                window.clsValue += entry.value;
              }
            }
          }
        });
        
        observer.observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
      }
    });
  }

  async measurePageLoad(url, testName) {
    console.log(`🔍 Measuring performance for: ${testName}`);
    
    const startTime = performance.now();
    
    // Navigate to page
    await this.page.goto(url);
    
    // Wait for network idle
    await this.page.waitForLoadState('networkidle');
    
    const endTime = performance.now();
    const loadTime = endTime - startTime;
    
    // Get Web Vitals
    const webVitals = await this.page.evaluate(() => {
      return {
        fcp: window.performance.getEntriesByName('first-contentful-paint')[0]?.startTime || 0,
        lcp: window.lcpValue || 0,
        fid: window.fidValue || 0,
        cls: window.clsValue || 0
      };
    });
    
    // Get resource loading metrics
    const resourceMetrics = await this.page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      const resources = performance.getEntriesByType('resource');
      
      return {
        domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
        domComplete: navigation.loadEventEnd - navigation.loadEventStart,
        totalResources: resources.length,
        totalResourceSize: resources.reduce((sum, resource) => sum + (resource.transferSize || 0), 0)
      };
    });
    
    const testResult = {
      name: testName,
      url: url,
      timestamp: new Date().toISOString(),
      loadTime: loadTime,
      webVitals: webVitals,
      resourceMetrics: resourceMetrics,
      thresholds: this.thresholds,
      passed: true,
      warnings: [],
      errors: []
    };
    
    // Check against thresholds
    if (loadTime > this.thresholds.dashboardLoad) {
      testResult.passed = false;
      testResult.errors.push(`Load time ${loadTime}ms exceeds threshold ${this.thresholds.dashboardLoad}ms`);
    } else if (loadTime > this.thresholds.dashboardLoad * 0.8) {
      testResult.warnings.push(`Load time ${loadTime}ms approaching threshold ${this.thresholds.dashboardLoad}ms`);
    }
    
    if (webVitals.fcp > this.thresholds.firstContentfulPaint) {
      testResult.passed = false;
      testResult.errors.push(`FCP ${webVitals.fcp}ms exceeds threshold ${this.thresholds.firstContentfulPaint}ms`);
    }
    
    if (webVitals.lcp > this.thresholds.largestContentfulPaint) {
      testResult.passed = false;
      testResult.errors.push(`LCP ${webVitals.lcp}ms exceeds threshold ${this.thresholds.largestContentfulPaint}ms`);
    }
    
    if (webVitals.cls > this.thresholds.cumulativeLayoutShift) {
      testResult.passed = false;
      testResult.errors.push(`CLS ${webVitals.cls} exceeds threshold ${this.thresholds.cumulativeLayoutShift}`);
    }
    
    if (webVitals.fid > this.thresholds.firstInputDelay) {
      testResult.passed = false;
      testResult.errors.push(`FID ${webVitals.fid}ms exceeds threshold ${this.thresholds.firstInputDelay}ms`);
    }
    
    // Update summary
    this.results.summary.totalTests++;
    if (testResult.passed) {
      this.results.summary.passed++;
    } else {
      this.results.summary.failed++;
    }
    
    if (testResult.warnings.length > 0) {
      this.results.summary.warnings++;
    }
    
    this.results.tests.push(testResult);
    
    console.log(`${testResult.passed ? '✅' : '❌'} ${testName} - Load: ${Math.round(loadTime)}ms`);
    
    return testResult;
  }

  async measureInteractionPerformance() {
    console.log('🔍 Measuring interaction performance...');
    
    await this.page.goto('http://localhost:3000');
    await this.page.waitForLoadState('networkidle');
    
    // Measure search performance
    const searchStartTime = performance.now();
    await this.page.fill('[data-testid="search-input"]', 'judiciary');
    await this.page.waitForTimeout(1000);
    const searchEndTime = performance.now();
    const searchTime = searchEndTime - searchStartTime;
    
    // Measure filter performance
    const filterStartTime = performance.now();
    await this.page.click('[data-testid="filter-toggle"]');
    await this.page.waitForSelector('[data-testid="status-filter"]');
    const filterEndTime = performance.now();
    const filterTime = filterEndTime - filterStartTime;
    
    // Measure sort performance
    const sortStartTime = performance.now();
    await this.page.selectOption('[data-testid="sort-select"]', 'committee');
    await this.page.waitForTimeout(500);
    const sortEndTime = performance.now();
    const sortTime = sortEndTime - sortStartTime;
    
    const interactionResult = {
      name: 'Interaction Performance',
      timestamp: new Date().toISOString(),
      searchTime: searchTime,
      filterTime: filterTime,
      sortTime: sortTime,
      passed: true,
      warnings: [],
      errors: []
    };
    
    // Check interaction thresholds
    if (searchTime > this.thresholds.searchResponse) {
      interactionResult.passed = false;
      interactionResult.errors.push(`Search response ${searchTime}ms exceeds threshold ${this.thresholds.searchResponse}ms`);
    }
    
    if (filterTime > this.thresholds.filterResponse) {
      interactionResult.passed = false;
      interactionResult.errors.push(`Filter response ${filterTime}ms exceeds threshold ${this.thresholds.filterResponse}ms`);
    }
    
    // Update summary
    this.results.summary.totalTests++;
    if (interactionResult.passed) {
      this.results.summary.passed++;
    } else {
      this.results.summary.failed++;
    }
    
    this.results.tests.push(interactionResult);
    
    console.log(`${interactionResult.passed ? '✅' : '❌'} Interaction Performance - Search: ${Math.round(searchTime)}ms, Filter: ${Math.round(filterTime)}ms`);
    
    return interactionResult;
  }

  async checkPerformanceRegression() {
    console.log('🔍 Checking for performance regression...');
    
    if (!fs.existsSync(this.baselineFile)) {
      console.log('📊 No baseline found, creating new baseline...');
      return this.createBaseline();
    }
    
    const baseline = JSON.parse(fs.readFileSync(this.baselineFile, 'utf8'));
    const currentResults = this.results.tests;
    
    for (const currentTest of currentResults) {
      const baselineTest = baseline.tests.find(t => t.name === currentTest.name);
      
      if (baselineTest) {
        const loadTimeIncrease = currentTest.loadTime - baselineTest.loadTime;
        const percentageIncrease = (loadTimeIncrease / baselineTest.loadTime) * 100;
        
        if (percentageIncrease > 20) { // 20% regression threshold
          const alert = {
            type: 'performance_regression',
            test: currentTest.name,
            baseline: baselineTest.loadTime,
            current: currentTest.loadTime,
            increase: loadTimeIncrease,
            percentageIncrease: percentageIncrease,
            timestamp: new Date().toISOString()
          };
          
          this.results.alerts.push(alert);
          console.log(`🚨 PERFORMANCE REGRESSION DETECTED: ${currentTest.name}`);
          console.log(`   Baseline: ${Math.round(baselineTest.loadTime)}ms`);
          console.log(`   Current: ${Math.round(currentTest.loadTime)}ms`);
          console.log(`   Increase: ${Math.round(loadTimeIncrease)}ms (${Math.round(percentageIncrease)}%)`);
        }
      }
    }
    
    return this.results.alerts;
  }

  async createBaseline() {
    console.log('📊 Creating performance baseline...');
    
    const baseline = {
      timestamp: new Date().toISOString(),
      tests: this.results.tests,
      thresholds: this.thresholds,
      version: '1.0.0'
    };
    
    fs.writeFileSync(this.baselineFile, JSON.stringify(baseline, null, 2));
    console.log(`✅ Baseline created: ${this.baselineFile}`);
    
    return baseline;
  }

  async updateHistory() {
    console.log('📈 Updating performance history...');
    
    let history = [];
    if (fs.existsSync(this.historyFile)) {
      history = JSON.parse(fs.readFileSync(this.historyFile, 'utf8'));
    }
    
    // Add current results to history
    history.push({
      timestamp: this.results.timestamp,
      summary: this.results.summary,
      tests: this.results.tests.map(t => ({
        name: t.name,
        loadTime: t.loadTime,
        webVitals: t.webVitals,
        passed: t.passed
      }))
    });
    
    // Keep last 100 runs
    if (history.length > 100) {
      history = history.slice(-100);
    }
    
    fs.writeFileSync(this.historyFile, JSON.stringify(history, null, 2));
    console.log(`✅ History updated: ${this.historyFile}`);
  }

  async generatePerformanceReport() {
    const reportPath = path.join(this.outputDir, 'performance_report.html');
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Performance Monitoring Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #2A2B32; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric.good { border-left: 4px solid #4ECDC4; }
        .metric.warning { border-left: 4px solid #FFA500; }
        .metric.bad { border-left: 4px solid #FF4444; }
        .test-result { margin-bottom: 20px; padding: 15px; border-radius: 8px; background: #f8f9fa; }
        .test-result.passed { border-left: 4px solid #4ECDC4; }
        .test-result.failed { border-left: 4px solid #FF4444; }
        .alert { background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 8px; margin: 10px 0; }
        .vital-metric { display: inline-block; margin: 5px 10px; }
        .vital-metric .label { font-weight: bold; color: #666; }
        .vital-metric .value { font-size: 18px; color: #2A2B32; }
        .thresholds { background: #e9ecef; padding: 10px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚡ Performance Monitoring Report</h1>
            <p>Senate Hearing Transcription System - Performance Baseline & Regression Detection</p>
            <p>Generated: ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="metrics">
            <div class="metric ${this.results.summary.failed === 0 ? 'good' : 'bad'}">
                <h3>${this.results.summary.passed}/${this.results.summary.totalTests}</h3>
                <p>Tests Passed</p>
            </div>
            <div class="metric ${this.results.summary.warnings === 0 ? 'good' : 'warning'}">
                <h3>${this.results.summary.warnings}</h3>
                <p>Warnings</p>
            </div>
            <div class="metric ${this.results.alerts.length === 0 ? 'good' : 'bad'}">
                <h3>${this.results.alerts.length}</h3>
                <p>Regression Alerts</p>
            </div>
        </div>
        
        ${this.results.alerts.length > 0 ? `
        <h2>🚨 Performance Alerts</h2>
        ${this.results.alerts.map(alert => `
            <div class="alert">
                <strong>Performance Regression: ${alert.test}</strong><br>
                Baseline: ${Math.round(alert.baseline)}ms → Current: ${Math.round(alert.current)}ms<br>
                Increase: ${Math.round(alert.increase)}ms (${Math.round(alert.percentageIncrease)}%)
            </div>
        `).join('')}
        ` : ''}
        
        <h2>📊 Performance Test Results</h2>
        ${this.results.tests.map(test => `
            <div class="test-result ${test.passed ? 'passed' : 'failed'}">
                <h3>${test.name}</h3>
                <p><strong>Load Time:</strong> ${Math.round(test.loadTime)}ms</p>
                
                ${test.webVitals ? `
                <div class="vital-metric">
                    <div class="label">FCP</div>
                    <div class="value">${Math.round(test.webVitals.fcp)}ms</div>
                </div>
                <div class="vital-metric">
                    <div class="label">LCP</div>
                    <div class="value">${Math.round(test.webVitals.lcp)}ms</div>
                </div>
                <div class="vital-metric">
                    <div class="label">CLS</div>
                    <div class="value">${test.webVitals.cls.toFixed(3)}</div>
                </div>
                <div class="vital-metric">
                    <div class="label">FID</div>
                    <div class="value">${Math.round(test.webVitals.fid)}ms</div>
                </div>
                ` : ''}
                
                ${test.searchTime ? `
                <div class="vital-metric">
                    <div class="label">Search</div>
                    <div class="value">${Math.round(test.searchTime)}ms</div>
                </div>
                <div class="vital-metric">
                    <div class="label">Filter</div>
                    <div class="value">${Math.round(test.filterTime)}ms</div>
                </div>
                ` : ''}
                
                ${test.errors.length > 0 ? `
                <div style="color: #dc3545; margin-top: 10px;">
                    <strong>Errors:</strong><br>
                    ${test.errors.join('<br>')}
                </div>
                ` : ''}
                
                ${test.warnings.length > 0 ? `
                <div style="color: #ffc107; margin-top: 10px;">
                    <strong>Warnings:</strong><br>
                    ${test.warnings.join('<br>')}
                </div>
                ` : ''}
            </div>
        `).join('')}
        
        <h2>⚙️ Performance Thresholds</h2>
        <div class="thresholds">
            <p><strong>Dashboard Load:</strong> ${this.thresholds.dashboardLoad}ms</p>
            <p><strong>Hearing Page Load:</strong> ${this.thresholds.hearingPageLoad}ms</p>
            <p><strong>Search Response:</strong> ${this.thresholds.searchResponse}ms</p>
            <p><strong>Filter Response:</strong> ${this.thresholds.filterResponse}ms</p>
            <p><strong>First Contentful Paint:</strong> ${this.thresholds.firstContentfulPaint}ms</p>
            <p><strong>Largest Contentful Paint:</strong> ${this.thresholds.largestContentfulPaint}ms</p>
            <p><strong>Cumulative Layout Shift:</strong> ${this.thresholds.cumulativeLayoutShift}</p>
            <p><strong>First Input Delay:</strong> ${this.thresholds.firstInputDelay}ms</p>
        </div>
    </div>
</body>
</html>
    `;
    
    fs.writeFileSync(reportPath, html);
    console.log(`✅ Performance report generated: ${reportPath}`);
  }

  async runAllTests() {
    console.log('🚀 Starting Performance Monitoring Suite...');
    
    try {
      await this.init();
      
      // Run performance tests
      await this.measurePageLoad('http://localhost:3000', 'Dashboard Load');
      await this.measurePageLoad('http://localhost:3000/hearings/12', 'Hearing Page Load');
      await this.measureInteractionPerformance();
      
      // Check for regressions
      await this.checkPerformanceRegression();
      
      // Update history
      await this.updateHistory();
      
      // Generate reports
      await this.generatePerformanceReport();
      
      // Save results
      const resultsPath = path.join(this.outputDir, 'performance_results.json');
      fs.writeFileSync(resultsPath, JSON.stringify(this.results, null, 2));
      
      console.log('\n🎉 Performance Monitoring Complete!');
      console.log(`📊 Results: ${this.results.summary.passed}/${this.results.summary.totalTests} tests passed`);
      console.log(`🚨 Alerts: ${this.results.alerts.length} regression alerts`);
      
      if (this.results.alerts.length > 0) {
        console.log('\n🚨 PERFORMANCE ALERTS:');
        this.results.alerts.forEach(alert => {
          console.log(`   ${alert.test}: ${Math.round(alert.percentageIncrease)}% regression`);
        });
      }
      
    } catch (error) {
      console.error('Performance monitoring failed:', error);
      throw error;
    } finally {
      if (this.browser) {
        await this.browser.close();
      }
    }
  }
}

// Run if called directly
if (require.main === module) {
  const monitor = new PerformanceMonitor();
  monitor.runAllTests().catch(error => {
    console.error('Performance monitoring execution failed:', error);
    process.exit(1);
  });
}

module.exports = PerformanceMonitor;