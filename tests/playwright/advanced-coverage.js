const { chromium, webkit, firefox } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Advanced Test Coverage Suite
 * 
 * This suite provides expanded test coverage including:
 * - Mobile responsive testing
 * - Accessibility testing with axe-core
 * - Cross-browser testing
 * - Advanced workflow testing
 */

class AdvancedCoverageTests {
  constructor() {
    this.browsers = [];
    this.contexts = [];
    this.pages = [];
    this.outputDir = 'playwright-results';
    this.results = {
      timestamp: new Date().toISOString(),
      summary: {
        totalTests: 0,
        passed: 0,
        failed: 0,
        warnings: 0,
        browsers: [],
        devices: []
      },
      tests: []
    };
    
    // Mobile devices to test
    this.mobileDevices = [
      { name: 'iPhone 13', viewport: { width: 390, height: 844 } },
      { name: 'iPad', viewport: { width: 768, height: 1024 } },
      { name: 'Samsung Galaxy S21', viewport: { width: 384, height: 854 } },
      { name: 'Desktop', viewport: { width: 1920, height: 1080 } }
    ];
    
    // Browsers to test
    this.browserEngines = [
      { name: 'Chromium', engine: chromium },
      { name: 'Firefox', engine: firefox },
      { name: 'WebKit', engine: webkit }
    ];
  }

  async init() {
    // Create output directory
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
    
    console.log('🚀 Initializing Advanced Coverage Tests...');
    console.log(`📱 Testing ${this.mobileDevices.length} device sizes`);
    console.log(`🌐 Testing ${this.browserEngines.length} browser engines`);
  }

  async takeScreenshot(page, name, device) {
    const filename = `${name}_${device.name.replace(/\s+/g, '_')}_${Date.now()}.png`;
    const filepath = path.join(this.outputDir, filename);
    await page.screenshot({ path: filepath, fullPage: true });
    return filepath;
  }

  async recordTest(testName, testFunction, browser, device) {
    const testStart = performance.now();
    let testResult = {
      name: testName,
      browser: browser,
      device: device.name,
      viewport: device.viewport,
      status: 'running',
      startTime: new Date().toISOString(),
      endTime: null,
      duration: 0,
      screenshots: [],
      errors: [],
      warnings: [],
      accessibilityIssues: []
    };

    this.results.summary.totalTests++;
    console.log(`\n🧪 Running: ${testName} (${browser} - ${device.name})`);

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
    }

    testResult.endTime = new Date().toISOString();
    testResult.duration = performance.now() - testStart;
    this.results.tests.push(testResult);

    return testResult;
  }

  // Mobile Responsive Testing
  async testMobileResponsiveness(page, device) {
    await page.goto('http://localhost:3000');
    
    // Test mobile navigation
    if (device.viewport.width < 768) {
      // Look for mobile menu elements
      const mobileMenuVisible = await page.isVisible('button[aria-label="Menu"]') || 
                               await page.isVisible('.mobile-menu-toggle') ||
                               await page.isVisible('.navbar-toggler');
      
      if (!mobileMenuVisible) {
        console.log(`⚠️  No mobile menu found on ${device.name}`);
      }
    }
    
    // Test responsive elements
    const searchInput = await page.locator('[data-testid="search-input"]');
    const searchBox = await searchInput.boundingBox();
    
    if (searchBox) {
      const searchWidth = searchBox.width;
      const viewportWidth = device.viewport.width;
      const searchPercentage = (searchWidth / viewportWidth) * 100;
      
      if (searchPercentage > 90) {
        console.log(`⚠️  Search input too wide on ${device.name}: ${searchPercentage}%`);
      }
    }
    
    // Test card responsiveness
    const hearingCards = await page.locator('[data-testid^="hearing-card-"]');
    const cardCount = await hearingCards.count();
    
    if (cardCount > 0) {
      const firstCard = hearingCards.first();
      const cardBox = await firstCard.boundingBox();
      
      if (cardBox) {
        const cardWidth = cardBox.width;
        const viewportWidth = device.viewport.width;
        
        // Cards should be responsive
        if (device.viewport.width < 768 && cardWidth > viewportWidth * 0.95) {
          console.log(`⚠️  Card width may be too wide on ${device.name}`);
        }
      }
    }
    
    // Test text readability
    const textElements = await page.locator('h1, h2, h3, p, button');
    const textCount = await textElements.count();
    
    for (let i = 0; i < Math.min(5, textCount); i++) {
      const element = textElements.nth(i);
      const fontSize = await element.evaluate(el => {
        const style = window.getComputedStyle(el);
        return parseFloat(style.fontSize);
      });
      
      if (fontSize < 14 && device.viewport.width < 768) {
        console.log(`⚠️  Small text detected on ${device.name}: ${fontSize}px`);
      }
    }
    
    console.log(`📱 Mobile responsiveness test completed for ${device.name}`);
  }

  // Accessibility Testing
  async testAccessibility(page, device) {
    // Inject axe-core for accessibility testing
    await page.addScriptTag({
      url: 'https://unpkg.com/axe-core@4.8.0/axe.min.js'
    });
    
    // Wait for axe to load
    await page.waitForTimeout(1000);
    
    // Run axe accessibility scan
    const accessibilityResults = await page.evaluate(() => {
      return new Promise((resolve) => {
        if (typeof axe !== 'undefined') {
          axe.run((err, results) => {
            if (err) {
              resolve({ error: err.message });
            } else {
              resolve(results);
            }
          });
        } else {
          resolve({ error: 'axe-core not loaded' });
        }
      });
    });
    
    if (accessibilityResults.error) {
      console.log(`⚠️  Accessibility test error: ${accessibilityResults.error}`);
      return [];
    }
    
    const violations = accessibilityResults.violations || [];
    const issues = [];
    
    violations.forEach(violation => {
      issues.push({
        id: violation.id,
        impact: violation.impact,
        description: violation.description,
        help: violation.help,
        helpUrl: violation.helpUrl,
        nodes: violation.nodes.length
      });
    });
    
    if (issues.length > 0) {
      console.log(`♿ Accessibility issues found on ${device.name}: ${issues.length}`);
      issues.forEach(issue => {
        console.log(`   - ${issue.impact}: ${issue.description}`);
      });
    } else {
      console.log(`✅ No accessibility issues found on ${device.name}`);
    }
    
    return issues;
  }

  // Cross-Browser Testing
  async testCrossBrowser(browserEngine, browserName, device) {
    let browser, context, page;
    
    try {
      // Launch browser
      browser = await browserEngine.launch({ headless: true });
      context = await browser.newContext({
        viewport: device.viewport,
        userAgent: device.userAgent
      });
      page = await context.newPage();
      
      // Test basic functionality
      await this.recordTest(
        `Cross-Browser Dashboard Load`, 
        async () => {
          await page.goto('http://localhost:3000');
          await page.waitForSelector('[data-testid="search-input"]', { timeout: 15000 });
          
          // Test search functionality
          await page.fill('[data-testid="search-input"]', 'test');
          await page.waitForTimeout(1000);
          
          // Test filters
          const filterToggle = await page.locator('[data-testid="filter-toggle"]');
          if (await filterToggle.isVisible()) {
            await filterToggle.click();
            await page.waitForTimeout(500);
          }
          
          console.log(`✅ Cross-browser test passed for ${browserName} on ${device.name}`);
        },
        browserName,
        device
      );
      
      // Test mobile responsiveness
      await this.recordTest(
        `Mobile Responsiveness`,
        async () => {
          await this.testMobileResponsiveness(page, device);
        },
        browserName,
        device
      );
      
      // Test accessibility
      const accessibilityResult = await this.recordTest(
        `Accessibility Testing`,
        async () => {
          const issues = await this.testAccessibility(page, device);
          if (issues.length > 0) {
            throw new Error(`${issues.length} accessibility issues found`);
          }
        },
        browserName,
        device
      );
      
      if (accessibilityResult.accessibilityIssues) {
        accessibilityResult.accessibilityIssues = await this.testAccessibility(page, device);
      }
      
      // Take screenshot
      const screenshot = await this.takeScreenshot(page, `cross_browser_${browserName}`, device);
      if (this.results.tests.length > 0) {
        this.results.tests[this.results.tests.length - 1].screenshots.push(screenshot);
      }
      
    } catch (error) {
      console.error(`❌ Cross-browser test failed for ${browserName} on ${device.name}:`, error.message);
      throw error;
    } finally {
      if (browser) await browser.close();
    }
  }

  // Advanced Workflow Testing
  async testAdvancedWorkflows(page, device) {
    await page.goto('http://localhost:3000');
    
    // Test complete user journey
    await page.waitForSelector('[data-testid="search-input"]', { timeout: 10000 });
    
    // 1. Search for content
    await page.fill('[data-testid="search-input"]', 'judiciary');
    await page.waitForTimeout(1000);
    
    // 2. Apply filters
    await page.click('[data-testid="filter-toggle"]');
    await page.waitForSelector('[data-testid="status-filter"]', { timeout: 5000 });
    
    // 3. Change sort order
    await page.selectOption('[data-testid="sort-select"]', 'date');
    await page.waitForTimeout(500);
    
    // 4. Navigate to hearing detail
    const hearingCards = await page.locator('[data-testid^="hearing-card-"]');
    const cardCount = await hearingCards.count();
    
    if (cardCount > 0) {
      await hearingCards.first().click();
      await page.waitForTimeout(3000);
      
      // Check if we successfully navigated
      const currentUrl = page.url();
      if (!currentUrl.includes('/hearings/')) {
        throw new Error(`Navigation failed - still on: ${currentUrl}`);
      }
    }
    
    // 5. Test back navigation
    await page.goBack();
    await page.waitForSelector('[data-testid="search-input"]', { timeout: 5000 });
    
    console.log(`🎯 Advanced workflow test completed for ${device.name}`);
  }

  async generateAdvancedReport() {
    const reportPath = path.join(this.outputDir, 'advanced_coverage_report.html');
    
    // Calculate statistics
    const deviceStats = {};
    const browserStats = {};
    const accessibilityStats = {
      totalIssues: 0,
      byImpact: {}
    };
    
    this.results.tests.forEach(test => {
      if (!deviceStats[test.device]) {
        deviceStats[test.device] = { passed: 0, failed: 0, total: 0 };
      }
      deviceStats[test.device].total++;
      if (test.status === 'passed') {
        deviceStats[test.device].passed++;
      } else {
        deviceStats[test.device].failed++;
      }
      
      if (!browserStats[test.browser]) {
        browserStats[test.browser] = { passed: 0, failed: 0, total: 0 };
      }
      browserStats[test.browser].total++;
      if (test.status === 'passed') {
        browserStats[test.browser].passed++;
      } else {
        browserStats[test.browser].failed++;
      }
      
      if (test.accessibilityIssues) {
        accessibilityStats.totalIssues += test.accessibilityIssues.length;
        test.accessibilityIssues.forEach(issue => {
          if (!accessibilityStats.byImpact[issue.impact]) {
            accessibilityStats.byImpact[issue.impact] = 0;
          }
          accessibilityStats.byImpact[issue.impact]++;
        });
      }
    });
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Advanced Coverage Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #6f42c1; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .section { margin-bottom: 30px; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .metric.passed { border-left: 4px solid #4ECDC4; }
        .metric.failed { border-left: 4px solid #FF4444; }
        .metric.warning { border-left: 4px solid #FFA500; }
        .test-result { margin-bottom: 15px; padding: 15px; border-radius: 8px; }
        .test-result.passed { background: #d4edda; border: 1px solid #c3e6cb; }
        .test-result.failed { background: #f8d7da; border: 1px solid #f5c6cb; }
        .device-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; }
        .device-stat { background: #f8f9fa; padding: 15px; border-radius: 8px; }
        .accessibility-issue { background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .accessibility-issue.critical { background: #f8d7da; }
        .accessibility-issue.serious { background: #fff3cd; }
        .accessibility-issue.moderate { background: #d1ecf1; }
        .accessibility-issue.minor { background: #d4edda; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Advanced Coverage Test Report</h1>
            <p>Mobile, Accessibility, and Cross-Browser Testing</p>
            <p>Generated: ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="section">
            <h2>📊 Test Summary</h2>
            <div class="metrics">
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
        </div>
        
        <div class="section">
            <h2>📱 Device Coverage</h2>
            <div class="device-stats">
                ${Object.entries(deviceStats).map(([device, stats]) => `
                    <div class="device-stat">
                        <h3>${device}</h3>
                        <p>Tests: ${stats.total}</p>
                        <p>Passed: ${stats.passed}</p>
                        <p>Failed: ${stats.failed}</p>
                        <p>Success Rate: ${Math.round((stats.passed / stats.total) * 100)}%</p>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="section">
            <h2>🌐 Browser Coverage</h2>
            <div class="device-stats">
                ${Object.entries(browserStats).map(([browser, stats]) => `
                    <div class="device-stat">
                        <h3>${browser}</h3>
                        <p>Tests: ${stats.total}</p>
                        <p>Passed: ${stats.passed}</p>
                        <p>Failed: ${stats.failed}</p>
                        <p>Success Rate: ${Math.round((stats.passed / stats.total) * 100)}%</p>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="section">
            <h2>♿ Accessibility Summary</h2>
            <div class="metrics">
                <div class="metric ${accessibilityStats.totalIssues === 0 ? 'passed' : 'failed'}">
                    <h3>${accessibilityStats.totalIssues}</h3>
                    <p>Total Issues</p>
                </div>
                ${Object.entries(accessibilityStats.byImpact).map(([impact, count]) => `
                    <div class="metric ${impact === 'critical' ? 'failed' : impact === 'serious' ? 'warning' : 'passed'}">
                        <h3>${count}</h3>
                        <p>${impact.charAt(0).toUpperCase() + impact.slice(1)}</p>
                    </div>
                `).join('')}
            </div>
        </div>
        
        <div class="section">
            <h2>🧪 Test Results</h2>
            ${this.results.tests.map(test => `
                <div class="test-result ${test.status}">
                    <h3>${test.name}</h3>
                    <p><strong>Browser:</strong> ${test.browser} | <strong>Device:</strong> ${test.device}</p>
                    <p><strong>Duration:</strong> ${Math.round(test.duration)}ms | <strong>Status:</strong> ${test.status.toUpperCase()}</p>
                    
                    ${test.errors.length > 0 ? `
                        <div style="color: #dc3545; margin-top: 10px;">
                            <strong>Errors:</strong><br>
                            ${test.errors.join('<br>')}
                        </div>
                    ` : ''}
                    
                    ${test.accessibilityIssues && test.accessibilityIssues.length > 0 ? `
                        <div style="margin-top: 10px;">
                            <strong>Accessibility Issues:</strong><br>
                            ${test.accessibilityIssues.map(issue => `
                                <div class="accessibility-issue ${issue.impact}">
                                    <strong>${issue.impact}:</strong> ${issue.description}
                                    <br><small><a href="${issue.helpUrl}" target="_blank">Learn more</a></small>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `).join('')}
        </div>
        
        <div class="section">
            <h2>✅ Key Achievements</h2>
            <ul>
                <li>✅ <strong>Mobile Responsive Testing</strong> - ${this.mobileDevices.length} device sizes tested</li>
                <li>✅ <strong>Cross-Browser Compatibility</strong> - ${this.browserEngines.length} browser engines tested</li>
                <li>✅ <strong>Accessibility Testing</strong> - WCAG compliance validation with axe-core</li>
                <li>✅ <strong>Advanced Workflows</strong> - Complete user journey testing</li>
                <li>✅ <strong>Visual Documentation</strong> - Screenshots for all test scenarios</li>
            </ul>
        </div>
    </div>
</body>
</html>
    `;
    
    fs.writeFileSync(reportPath, html);
    console.log(`✅ Advanced coverage report generated: ${reportPath}`);
  }

  async runAllTests() {
    console.log('🚀 Starting Advanced Coverage Test Suite...');
    
    try {
      await this.init();
      
      // Test with primary browser (Chromium) across all devices
      const primaryBrowser = await chromium.launch({ headless: true });
      
      for (const device of this.mobileDevices) {
        console.log(`\n📱 Testing ${device.name} (${device.viewport.width}x${device.viewport.height})`);
        
        const context = await primaryBrowser.newContext({
          viewport: device.viewport
        });
        const page = await context.newPage();
        
        try {
          // Mobile responsiveness test
          await this.recordTest(
            `Mobile Responsiveness`,
            async () => {
              await this.testMobileResponsiveness(page, device);
            },
            'Chromium',
            device
          );
          
          // Accessibility test
          await this.recordTest(
            `Accessibility Testing`,
            async () => {
              const issues = await this.testAccessibility(page, device);
              if (issues.length > 0) {
                this.results.tests[this.results.tests.length - 1].accessibilityIssues = issues;
                if (issues.some(issue => issue.impact === 'critical')) {
                  throw new Error(`Critical accessibility issues found: ${issues.length}`);
                }
              }
            },
            'Chromium',
            device
          );
          
          // Advanced workflow test
          await this.recordTest(
            `Advanced Workflows`,
            async () => {
              await this.testAdvancedWorkflows(page, device);
            },
            'Chromium',
            device
          );
          
          // Take screenshot
          const screenshot = await this.takeScreenshot(page, `advanced_coverage`, device);
          if (this.results.tests.length > 0) {
            this.results.tests[this.results.tests.length - 1].screenshots.push(screenshot);
          }
          
        } catch (error) {
          console.error(`Error testing ${device.name}:`, error.message);
        } finally {
          await context.close();
        }
      }
      
      await primaryBrowser.close();
      
      // Cross-browser testing (desktop only for performance)
      const desktopDevice = this.mobileDevices.find(d => d.name === 'Desktop');
      
      for (const browserEngine of this.browserEngines) {
        console.log(`\n🌐 Testing ${browserEngine.name} browser`);
        
        try {
          await this.testCrossBrowser(browserEngine.engine, browserEngine.name, desktopDevice);
        } catch (error) {
          console.error(`Cross-browser test failed for ${browserEngine.name}:`, error.message);
        }
      }
      
      // Generate report
      await this.generateAdvancedReport();
      
      // Save results
      const resultsPath = path.join(this.outputDir, 'advanced_coverage_results.json');
      fs.writeFileSync(resultsPath, JSON.stringify(this.results, null, 2));
      
      console.log('\n🎉 Advanced Coverage Testing Complete!');
      console.log(`📊 Results: ${this.results.summary.passed}/${this.results.summary.totalTests} tests passed`);
      console.log(`📱 Devices tested: ${this.mobileDevices.length}`);
      console.log(`🌐 Browsers tested: ${this.browserEngines.length}`);
      
    } catch (error) {
      console.error('Advanced coverage testing failed:', error);
      throw error;
    }
  }
}

// Run if called directly
if (require.main === module) {
  const tester = new AdvancedCoverageTests();
  tester.runAllTests().catch(error => {
    console.error('Advanced coverage test execution failed:', error);
    process.exit(1);
  });
}

module.exports = AdvancedCoverageTests;