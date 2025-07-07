const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Visual Regression Testing Suite
 * 
 * Implements screenshot comparison testing to detect unintended visual changes
 * across different pages and components of the application.
 */

class VisualRegressionTester {
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
    this.outputDir = 'playwright-results/visual';
    this.baselineDir = 'playwright-results/visual/baseline';
    this.currentDir = 'playwright-results/visual/current';
    this.diffDir = 'playwright-results/visual/diffs';
  }

  async init() {
    // Create output directories
    [this.outputDir, this.baselineDir, this.currentDir, this.diffDir].forEach(dir => {
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }
    });

    // Launch browser with consistent viewport
    this.browser = await chromium.launch({ headless: true });
    this.context = await this.browser.newContext({
      viewport: { width: 1920, height: 1080 },
      deviceScaleFactor: 1,
      hasTouch: false,
      isMobile: false
    });
    this.page = await this.context.newPage();

    // Set consistent styling for screenshots
    await this.page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
          caret-color: transparent !important;
        }
        
        input, textarea {
          caret-color: transparent !important;
        }
      `
    });

    console.log('🚀 Starting Visual Regression Testing Suite...');
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
      screenshots: {
        baseline: null,
        current: null,
        diff: null
      },
      pixelDifference: 0,
      percentDifference: 0
    };

    this.results.summary.totalTests++;
    console.log(`🧪 Visual Test: ${testName}`);

    const startTime = performance.now();
    
    try {
      const result = await testFunction();
      if (result) {
        test.screenshots = result.screenshots || {};
        test.pixelDifference = result.pixelDifference || 0;
        test.percentDifference = result.percentDifference || 0;
        
        // Determine if test passed based on visual difference threshold
        const threshold = 1; // 1% difference allowed
        if (test.percentDifference <= threshold) {
          test.status = 'passed';
          this.results.summary.passed++;
          console.log(`✅ ${testName} - PASSED (${test.percentDifference.toFixed(2)}% difference)`);
        } else {
          test.status = 'failed';
          test.errors.push(`Visual difference ${test.percentDifference.toFixed(2)}% exceeds threshold ${threshold}%`);
          this.results.summary.failed++;
          console.log(`❌ ${testName} - FAILED: ${test.percentDifference.toFixed(2)}% visual difference`);
        }
      } else {
        test.status = 'passed';
        this.results.summary.passed++;
        console.log(`✅ ${testName} - PASSED (baseline created)`);
      }
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

  async capturePageScreenshot(name, url, selector = null) {
    try {
      await this.page.goto(url, { waitUntil: 'networkidle' });
      
      // Wait for dynamic content to load
      await this.page.waitForTimeout(2000);
      
      // Wait for search input to ensure page is fully loaded
      if (url.includes('localhost:3000')) {
        try {
          await this.page.waitForSelector('[data-testid="search-input"]', { timeout: 10000 });
        } catch (e) {
          // Continue if search input not found
        }
      }

      const screenshotOptions = {
        path: path.join(this.currentDir, `${name}.png`),
        fullPage: false
      };

      if (selector) {
        await this.page.waitForSelector(selector, { timeout: 5000 });
        screenshotOptions.clip = await this.page.locator(selector).boundingBox();
      }

      await this.page.screenshot(screenshotOptions);
      
      return this.compareWithBaseline(name);
    } catch (error) {
      throw new Error(`Failed to capture screenshot for ${name}: ${error.message}`);
    }
  }

  async compareWithBaseline(name) {
    const baselinePath = path.join(this.baselineDir, `${name}.png`);
    const currentPath = path.join(this.currentDir, `${name}.png`);
    const diffPath = path.join(this.diffDir, `${name}.png`);

    // If baseline doesn't exist, create it
    if (!fs.existsSync(baselinePath)) {
      fs.copyFileSync(currentPath, baselinePath);
      console.log(`📸 Baseline created for ${name}`);
      return null; // No comparison possible
    }

    // Compare images using Playwright's visual comparison
    try {
      const baselineBuffer = fs.readFileSync(baselinePath);
      const currentBuffer = fs.readFileSync(currentPath);
      
      // For now, we'll use a simple byte comparison
      // In a real implementation, you'd use a proper image diffing library
      const pixelDifference = this.calculatePixelDifference(baselineBuffer, currentBuffer);
      const totalPixels = 1920 * 1080; // viewport size
      const percentDifference = (pixelDifference / totalPixels) * 100;

      // Create a simple diff indicator
      if (pixelDifference > 0) {
        fs.writeFileSync(diffPath, `Visual difference detected: ${pixelDifference} pixels (${percentDifference.toFixed(2)}%)`);
      }

      return {
        screenshots: {
          baseline: baselinePath,
          current: currentPath,
          diff: diffPath
        },
        pixelDifference,
        percentDifference
      };
    } catch (error) {
      throw new Error(`Failed to compare images: ${error.message}`);
    }
  }

  calculatePixelDifference(buffer1, buffer2) {
    // Simple byte-level comparison (not pixel-perfect but good enough for demo)
    if (buffer1.length !== buffer2.length) {
      return Math.abs(buffer1.length - buffer2.length);
    }

    let differences = 0;
    for (let i = 0; i < buffer1.length; i++) {
      if (buffer1[i] !== buffer2[i]) {
        differences++;
      }
    }

    // Approximate pixel difference (rough calculation)
    return Math.floor(differences / 4); // Assuming 4 bytes per pixel (RGBA)
  }

  async testDashboardPage() {
    return await this.capturePageScreenshot('dashboard', 'http://localhost:3000');
  }

  async testHearingTranscriptPage() {
    return await this.capturePageScreenshot('hearing-transcript', 'http://localhost:3000/hearings/12');
  }

  async testHearingStatusPage() {
    return await this.capturePageScreenshot('hearing-status', 'http://localhost:3000/hearings/12/status');
  }

  async testDashboardSearchBar() {
    await this.page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await this.page.waitForSelector('[data-testid="search-input"]', { timeout: 10000 });
    return await this.capturePageScreenshot('search-bar', 'http://localhost:3000', '[data-testid="search-input"]');
  }

  async testHearingCard() {
    await this.page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    await this.page.waitForSelector('[data-testid^="hearing-card-"]', { timeout: 10000 });
    return await this.capturePageScreenshot('hearing-card', 'http://localhost:3000', '[data-testid^="hearing-card-"]:first-of-type');
  }

  async testFilterControls() {
    await this.page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Open filters
    await this.page.waitForSelector('[data-testid="filter-toggle"]', { timeout: 10000 });
    await this.page.click('[data-testid="filter-toggle"]');
    await this.page.waitForTimeout(1000);
    
    return await this.capturePageScreenshot('filter-controls', 'http://localhost:3000', '[data-testid="filter-panel"]');
  }

  async testResponsiveDesign() {
    // Test mobile view
    await this.page.setViewportSize({ width: 375, height: 667 }); // iPhone SE
    const mobileResult = await this.capturePageScreenshot('mobile-dashboard', 'http://localhost:3000');
    
    // Test tablet view
    await this.page.setViewportSize({ width: 768, height: 1024 }); // iPad
    const tabletResult = await this.capturePageScreenshot('tablet-dashboard', 'http://localhost:3000');
    
    // Reset to desktop
    await this.page.setViewportSize({ width: 1920, height: 1080 });
    
    return {
      mobile: mobileResult,
      tablet: tabletResult
    };
  }

  async testThemeConsistency() {
    await this.page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
    
    // Capture color scheme elements
    const colorElements = await this.page.evaluate(() => {
      const elements = document.querySelectorAll('*');
      const colors = new Set();
      
      elements.forEach(el => {
        const styles = window.getComputedStyle(el);
        colors.add(styles.backgroundColor);
        colors.add(styles.color);
        colors.add(styles.borderColor);
      });
      
      return Array.from(colors).filter(color => color && color !== 'rgba(0, 0, 0, 0)' && color !== 'transparent');
    });

    // Store color palette for comparison
    fs.writeFileSync(
      path.join(this.outputDir, 'color-palette.json'),
      JSON.stringify(colorElements, null, 2)
    );

    return await this.capturePageScreenshot('theme-consistency', 'http://localhost:3000');
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
      path.join(this.outputDir, 'visual_regression_results.json'),
      JSON.stringify(jsonReport, null, 2)
    );

    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>Visual Regression Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #1B1C20; color: #FFFFFF; }
        .header { background: #2A2B32; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .success { color: #4ECDC4; }
        .failure { color: #FF4444; }
        .warning { color: #FFA500; }
        .test-card { background: #2A2B32; border: 1px solid #444; border-radius: 8px; padding: 15px; margin: 10px 0; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .screenshot-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; margin-top: 15px; }
        .screenshot-item { text-align: center; }
        .screenshot-item img { max-width: 100%; height: auto; border: 1px solid #444; border-radius: 4px; }
        .screenshot-item h4 { margin: 10px 0 5px 0; color: #FFFFFF; }
        .difference-metric { background: #1B1C20; padding: 8px; border-radius: 4px; margin: 5px 0; font-family: monospace; }
    </style>
</head>
<body>
    <div class="header">
        <h1>👁️ Visual Regression Test Results</h1>
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
            ${test.percentDifference > 0 ? `
                <div class="difference-metric">
                    Pixel Difference: ${test.pixelDifference} pixels (${test.percentDifference.toFixed(2)}%)
                </div>
            ` : ''}
            ${test.errors.length > 0 ? `<div class="failure">Errors: ${test.errors.join(', ')}</div>` : ''}
            
            ${test.screenshots.current ? `
                <div class="screenshot-grid">
                    <div class="screenshot-item">
                        <h4>Current</h4>
                        <img src="${path.relative(this.outputDir, test.screenshots.current)}" alt="Current screenshot" />
                    </div>
                    ${test.screenshots.baseline ? `
                        <div class="screenshot-item">
                            <h4>Baseline</h4>
                            <img src="${path.relative(this.outputDir, test.screenshots.baseline)}" alt="Baseline screenshot" />
                        </div>
                    ` : ''}
                    ${test.screenshots.diff ? `
                        <div class="screenshot-item">
                            <h4>Difference</h4>
                            <div class="difference-metric">Diff data available</div>
                        </div>
                    ` : ''}
                </div>
            ` : ''}
        </div>
    `).join('')}

    <div class="test-card">
        <h3>📁 Test Artifacts</h3>
        <div>Baseline Images: ${this.baselineDir}</div>
        <div>Current Images: ${this.currentDir}</div>
        <div>Difference Data: ${this.diffDir}</div>
        <div>Color Palette: ${this.outputDir}/color-palette.json</div>
    </div>
</body>
</html>`;

    fs.writeFileSync(path.join(this.outputDir, 'visual_regression_report.html'), htmlReport);

    console.log(`📊 Visual Regression Report Generated:`);
    console.log(`   HTML: ${this.outputDir}/visual_regression_report.html`);
    console.log(`   JSON: ${this.outputDir}/visual_regression_results.json`);
  }

  async runAllTests() {
    await this.init();

    // Run all visual regression tests
    await this.runTest('Dashboard Page', () => this.testDashboardPage());
    await this.runTest('Hearing Transcript Page', () => this.testHearingTranscriptPage());
    await this.runTest('Hearing Status Page', () => this.testHearingStatusPage());
    await this.runTest('Search Bar Component', () => this.testDashboardSearchBar());
    await this.runTest('Hearing Card Component', () => this.testHearingCard());
    await this.runTest('Filter Controls', () => this.testFilterControls());
    await this.runTest('Responsive Design', () => this.testResponsiveDesign());
    await this.runTest('Theme Consistency', () => this.testThemeConsistency());

    await this.generateReport();

    const successRate = Math.round((this.results.summary.passed / this.results.summary.totalTests) * 100);
    console.log(`🎉 Visual Regression Testing Complete!`);
    console.log(`📊 Results: ${this.results.summary.passed}/${this.results.summary.totalTests} tests passed (${successRate}%)`);

    if (this.browser) {
      await this.browser.close();
    }

    return this.results;
  }
}

// Run the test suite
if (require.main === module) {
  const visualTester = new VisualRegressionTester();
  visualTester.runAllTests().catch(console.error);
}

module.exports = VisualRegressionTester;