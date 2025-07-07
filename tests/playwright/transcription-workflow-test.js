const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

/**
 * Specific test for the transcription workflow issues identified in the conversation summary
 * 
 * Focus Areas:
 * 1. React null check errors (transcript.segments)
 * 2. TranscriptionWarnings errors (toFixed on undefined)
 * 3. API endpoint connection testing
 * 4. Threading/async issues monitoring
 */

class TranscriptionWorkflowTester {
  constructor() {
    this.browser = null;
    this.context = null;
    this.page = null;
    this.outputDir = 'playwright-results/transcription-workflow';
    this.consoleMessages = [];
    this.pageErrors = [];
    this.networkErrors = [];
  }

  async init() {
    // Create output directory
    fs.mkdirSync(this.outputDir, { recursive: true });

    // Launch browser with comprehensive logging
    this.browser = await chromium.launch({ 
      headless: false,
      devtools: true // Enable DevTools for debugging
    });
    
    this.context = await this.browser.newContext({
      recordVideo: { dir: this.outputDir },
      viewport: { width: 1920, height: 1080 }
    });
    
    this.page = await this.context.newPage();

    // Set up comprehensive logging
    this.page.on('console', msg => {
      const logEntry = {
        type: msg.type(),
        text: msg.text(),
        location: msg.location(),
        timestamp: new Date().toISOString()
      };
      this.consoleMessages.push(logEntry);
      
      if (msg.type() === 'error') {
        console.error(`🚨 [CONSOLE ERROR] ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        console.warn(`⚠️ [CONSOLE WARNING] ${msg.text()}`);
      }
    });

    // Set up error logging
    this.page.on('pageerror', error => {
      const errorEntry = {
        message: error.message,
        stack: error.stack,
        timestamp: new Date().toISOString()
      };
      this.pageErrors.push(errorEntry);
      console.error(`💥 [PAGE ERROR] ${error.message}`);
    });

    // Set up network monitoring
    this.page.on('response', response => {
      if (!response.ok()) {
        const networkError = {
          url: response.url(),
          status: response.status(),
          statusText: response.statusText(),
          timestamp: new Date().toISOString()
        };
        this.networkErrors.push(networkError);
        console.error(`🌐 [NETWORK ERROR] ${response.status()} ${response.url()}`);
      }
    });
  }

  async takeScreenshot(name) {
    const screenshotPath = path.join(this.outputDir, `${name}.png`);
    await this.page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`📸 Screenshot saved: ${screenshotPath}`);
    return screenshotPath;
  }

  async savePageContent(name) {
    const htmlPath = path.join(this.outputDir, `${name}.html`);
    const content = await this.page.content();
    fs.writeFileSync(htmlPath, content);
    console.log(`📄 Page content saved: ${htmlPath}`);
    return htmlPath;
  }

  async testTranscriptSegmentNullChecks() {
    console.log('\n🧪 Testing transcript segment null checks...');
    
    // Navigate to hearing transcript page
    await this.page.goto('http://localhost:3000/hearings/12/transcript');
    await this.page.waitForLoadState('networkidle');
    
    // Wait for React to render
    await this.page.waitForTimeout(3000);
    
    await this.takeScreenshot('transcript_page_loaded');
    
    // Check for specific React errors related to transcript.segments
    const reactErrors = this.consoleMessages.filter(msg => 
      msg.type === 'error' && 
      (msg.text.includes('Cannot read properties of undefined') ||
       msg.text.includes('transcript.segments') ||
       msg.text.includes('reading \'map\''))
    );
    
    if (reactErrors.length > 0) {
      console.error('❌ React null check errors found:', reactErrors);
      await this.savePageContent('react_error_page');
      return { success: false, errors: reactErrors };
    }
    
    // Check if transcript segments are properly displayed
    const transcriptSegments = await this.page.evaluate(() => {
      const segments = document.querySelectorAll('[data-testid="transcript-segment"], .transcript-segment, .segment');
      return {
        segmentCount: segments.length,
        hasSegments: segments.length > 0,
        segmentText: Array.from(segments).slice(0, 3).map(s => s.textContent?.substring(0, 100))
      };
    });
    
    console.log('📊 Transcript segments analysis:', transcriptSegments);
    
    return { success: true, data: transcriptSegments };
  }

  async testTranscriptionWarningsComponent() {
    console.log('\n🧪 Testing TranscriptionWarnings component...');
    
    // Navigate to a hearing that might trigger warnings
    await this.page.goto('http://localhost:3000/hearings/11');
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForTimeout(2000);
    
    await this.takeScreenshot('hearing_page_loaded');
    
    // Look for transcription buttons that might trigger warnings
    const transcriptionButtons = await this.page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      return buttons.filter(btn => 
        btn.textContent.toLowerCase().includes('transcribe') ||
        btn.textContent.toLowerCase().includes('process')
      ).map(btn => ({
        text: btn.textContent,
        disabled: btn.disabled,
        visible: btn.offsetParent !== null
      }));
    });
    
    console.log('🔘 Transcription buttons found:', transcriptionButtons);
    
    if (transcriptionButtons.length > 0) {
      // Try to click the first available transcription button
      try {
        await this.page.click('button:has-text("Transcribe")');
        await this.page.waitForTimeout(2000);
        
        // Check for toFixed errors
        const toFixedErrors = this.consoleMessages.filter(msg => 
          msg.type === 'error' && 
          msg.text.includes('toFixed')
        );
        
        if (toFixedErrors.length > 0) {
          console.error('❌ toFixed errors found:', toFixedErrors);
          await this.savePageContent('toFixed_error_page');
          return { success: false, errors: toFixedErrors };
        }
        
        await this.takeScreenshot('after_transcribe_click');
      } catch (error) {
        console.log('ℹ️ Transcribe button not clickable or not found:', error.message);
      }
    }
    
    return { success: true, warnings: transcriptionButtons.length === 0 ? ['No transcription buttons found'] : [] };
  }

  async testApiEndpoints() {
    console.log('\n🧪 Testing API endpoints...');
    
    const endpoints = [
      { url: 'http://localhost:8001/api/health', name: 'health' },
      { url: 'http://localhost:8001/api/hearings', name: 'hearings_list' },
      { url: 'http://localhost:8001/api/hearings/12', name: 'hearing_detail' },
      { url: 'http://localhost:8001/api/hearings/12/transcript', name: 'transcript' }
    ];
    
    const results = [];
    
    for (const endpoint of endpoints) {
      try {
        const response = await this.page.goto(endpoint.url);
        await this.page.waitForTimeout(1000);
        
        const responseText = await this.page.evaluate(() => document.body.textContent);
        
        results.push({
          endpoint: endpoint.name,
          url: endpoint.url,
          status: response.status(),
          success: response.ok(),
          responseLength: responseText.length,
          hasErrorMessage: responseText.toLowerCase().includes('error'),
          preview: responseText.substring(0, 200)
        });
        
        console.log(`✅ ${endpoint.name}: ${response.status()} (${responseText.length} chars)`);
        
      } catch (error) {
        results.push({
          endpoint: endpoint.name,
          url: endpoint.url,
          success: false,
          error: error.message
        });
        console.error(`❌ ${endpoint.name}: ${error.message}`);
      }
    }
    
    return { success: true, results };
  }

  async testThreadingIssues() {
    console.log('\n🧪 Testing for threading/async issues...');
    
    // Navigate to transcript page and monitor for async errors
    await this.page.goto('http://localhost:3000/hearings/12/transcript');
    await this.page.waitForLoadState('networkidle');
    
    // Wait longer to catch async issues
    await this.page.waitForTimeout(5000);
    
    // Check for threading-related errors
    const threadingErrors = this.consoleMessages.filter(msg => 
      msg.type === 'error' && 
      (msg.text.includes('current event loop') ||
       msg.text.includes('threading') ||
       msg.text.includes('async') ||
       msg.text.includes('Promise'))
    );
    
    if (threadingErrors.length > 0) {
      console.error('❌ Threading/async errors found:', threadingErrors);
      return { success: false, errors: threadingErrors };
    }
    
    return { success: true };
  }

  async generateReport() {
    const report = {
      timestamp: new Date().toISOString(),
      summary: {
        totalConsoleMessages: this.consoleMessages.length,
        totalPageErrors: this.pageErrors.length,
        totalNetworkErrors: this.networkErrors.length,
        consoleErrors: this.consoleMessages.filter(m => m.type === 'error').length,
        consoleWarnings: this.consoleMessages.filter(m => m.type === 'warning').length
      },
      consoleMessages: this.consoleMessages,
      pageErrors: this.pageErrors,
      networkErrors: this.networkErrors,
      analysis: {
        reactNullCheckErrors: this.consoleMessages.filter(m => 
          m.type === 'error' && m.text.includes('Cannot read properties of undefined')
        ),
        toFixedErrors: this.consoleMessages.filter(m => 
          m.type === 'error' && m.text.includes('toFixed')
        ),
        threadingErrors: this.consoleMessages.filter(m => 
          m.type === 'error' && m.text.includes('event loop')
        )
      }
    };
    
    const reportPath = path.join(this.outputDir, 'transcription_workflow_report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    // Generate HTML report
    const htmlReport = `
<!DOCTYPE html>
<html>
<head>
    <title>Transcription Workflow Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .error { background: #f8d7da; color: #721c24; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .warning { background: #fff3cd; color: #856404; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; padding: 10px; margin: 5px 0; border-radius: 4px; }
        .code { background: #f8f9fa; padding: 10px; border-radius: 4px; font-family: monospace; }
        .collapsible { cursor: pointer; background: #e9ecef; padding: 10px; border-radius: 4px; margin: 5px 0; }
        .content { display: none; padding: 10px; border-left: 3px solid #007bff; margin-left: 20px; }
    </style>
</head>
<body>
    <h1>Transcription Workflow Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Console Messages:</strong> ${report.summary.totalConsoleMessages}</p>
        <p><strong>Console Errors:</strong> ${report.summary.consoleErrors}</p>
        <p><strong>Console Warnings:</strong> ${report.summary.consoleWarnings}</p>
        <p><strong>Page Errors:</strong> ${report.summary.totalPageErrors}</p>
        <p><strong>Network Errors:</strong> ${report.summary.totalNetworkErrors}</p>
        <p><strong>React Null Check Errors:</strong> ${report.analysis.reactNullCheckErrors.length}</p>
        <p><strong>toFixed Errors:</strong> ${report.analysis.toFixedErrors.length}</p>
        <p><strong>Threading Errors:</strong> ${report.analysis.threadingErrors.length}</p>
    </div>
    
    <h2>Analysis</h2>
    ${report.analysis.reactNullCheckErrors.length > 0 ? `
        <div class="error">
            <h3>React Null Check Errors Found</h3>
            ${report.analysis.reactNullCheckErrors.map(error => `<div class="code">${error.text}</div>`).join('')}
        </div>
    ` : '<div class="success">No React null check errors found</div>'}
    
    ${report.analysis.toFixedErrors.length > 0 ? `
        <div class="error">
            <h3>toFixed Errors Found</h3>
            ${report.analysis.toFixedErrors.map(error => `<div class="code">${error.text}</div>`).join('')}
        </div>
    ` : '<div class="success">No toFixed errors found</div>'}
    
    ${report.analysis.threadingErrors.length > 0 ? `
        <div class="error">
            <h3>Threading Errors Found</h3>
            ${report.analysis.threadingErrors.map(error => `<div class="code">${error.text}</div>`).join('')}
        </div>
    ` : '<div class="success">No threading errors found</div>'}
    
    <h2>All Console Messages</h2>
    ${report.consoleMessages.map(msg => `
        <div class="${msg.type === 'error' ? 'error' : msg.type === 'warning' ? 'warning' : ''}">
            <strong>[${msg.type.toUpperCase()}]</strong> ${msg.text}
        </div>
    `).join('')}
    
    <script>
        document.querySelectorAll('.collapsible').forEach(el => {
            el.addEventListener('click', function() {
                this.classList.toggle('active');
                const content = this.nextElementSibling;
                content.style.display = content.style.display === 'block' ? 'none' : 'block';
            });
        });
    </script>
</body>
</html>
    `;
    
    const htmlReportPath = path.join(this.outputDir, 'transcription_workflow_report.html');
    fs.writeFileSync(htmlReportPath, htmlReport);
    
    console.log(`📊 Report generated: ${reportPath}`);
    console.log(`📄 HTML Report: ${htmlReportPath}`);
    
    return report;
  }

  async runAllTests() {
    console.log('🚀 Starting Transcription Workflow Tests...');
    
    await this.init();
    
    try {
      // Run all tests
      const testResults = {
        nullChecks: await this.testTranscriptSegmentNullChecks(),
        warnings: await this.testTranscriptionWarningsComponent(),
        apiEndpoints: await this.testApiEndpoints(),
        threading: await this.testThreadingIssues()
      };
      
      console.log('\n📊 Test Results Summary:');
      console.log('Null Checks:', testResults.nullChecks.success ? '✅ PASSED' : '❌ FAILED');
      console.log('Warnings:', testResults.warnings.success ? '✅ PASSED' : '❌ FAILED');
      console.log('API Endpoints:', testResults.apiEndpoints.success ? '✅ PASSED' : '❌ FAILED');
      console.log('Threading:', testResults.threading.success ? '✅ PASSED' : '❌ FAILED');
      
      // Generate comprehensive report
      const report = await this.generateReport();
      
      // Clean up
      await this.context.close();
      await this.browser.close();
      
      const overallSuccess = Object.values(testResults).every(result => result.success);
      
      console.log(`\n🎯 Overall Result: ${overallSuccess ? '✅ ALL TESTS PASSED' : '❌ SOME TESTS FAILED'}`);
      console.log(`📁 Results saved to: ${this.outputDir}/`);
      
      return { success: overallSuccess, testResults, report };
      
    } catch (error) {
      console.error('❌ Test execution failed:', error);
      await this.context.close();
      await this.browser.close();
      throw error;
    }
  }
}

// Run tests if called directly
if (require.main === module) {
  const tester = new TranscriptionWorkflowTester();
  tester.runAllTests().then(result => {
    process.exit(result.success ? 0 : 1);
  }).catch(error => {
    console.error('Test runner failed:', error);
    process.exit(1);
  });
}

module.exports = TranscriptionWorkflowTester;