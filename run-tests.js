const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const http = require('http');

/**
 * Enhanced test runner for Senate Hearing Transcription System
 * 
 * This combines the original page analysis with comprehensive testing
 * designed to break the broken loop problem.
 */

const config = JSON.parse(fs.readFileSync('playwright.config.json', 'utf8'));
const { baseUrl, pages, outputDir, testSettings } = config;

// Health check function
async function checkServerHealth(url) {
  return new Promise((resolve) => {
    const request = http.get(url, (res) => {
      if (res.statusCode === 200) {
        resolve(true);
      } else {
        resolve(false);
      }
    });
    request.on('error', () => resolve(false));
    request.setTimeout(5000, () => {
      request.destroy();
      resolve(false);
    });
  });
}

async function main() {
  const startTime = performance.now();
  console.log('🚀 Starting Senate Hearing Transcription System Test Suite...');
  
  // Clean up previous results
  if (fs.existsSync(outputDir)) {
    fs.rmSync(outputDir, { recursive: true, force: true });
  }
  fs.mkdirSync(outputDir, { recursive: true });

  // Health check servers
  if (testSettings && testSettings.waitForServer) {
    console.log('🏥 Checking server health...');
    
    const frontendHealthy = await checkServerHealth(testSettings.waitForServer.frontend);
    const backendHealthy = await checkServerHealth(testSettings.waitForServer.backend);
    
    if (!frontendHealthy) {
      console.error('❌ Frontend server not responsive:', testSettings.waitForServer.frontend);
      console.error('Please start the frontend server: cd dashboard && npm start');
      process.exit(1);
    }
    
    if (!backendHealthy) {
      console.error('❌ Backend server not responsive:', testSettings.waitForServer.backend);
      console.error('Please start the backend server: python simple_api_server.py');
      process.exit(1);
    }
    
    console.log('✅ All servers are responsive');
  }

  let hasErrors = false;
  const summary = [];

  // Run comprehensive tests first
  console.log('\n🧪 Running comprehensive test suite...');
  try {
    execSync('node tests/playwright/comprehensive-test.js', { stdio: 'inherit' });
    console.log('✅ Comprehensive tests completed successfully');
  } catch (error) {
    console.error('❌ Comprehensive tests failed:', error.message);
    hasErrors = true;
    summary.push({ 
      page: 'comprehensive_tests', 
      status: 'failed', 
      error: 'Comprehensive test suite failed',
      details: error.message 
    });
  }

  // Run original page analysis tests
  console.log('\n📄 Running page analysis tests...');
  for (const page of pages) {
    const url = `${baseUrl}${page.path}`;
    const pageOutputDir = path.join(outputDir, page.name);
    
    try {
      console.log(`Analyzing page: ${url}`);
      execSync(`node analyze-page.js "${url}" "${pageOutputDir}"`, { stdio: 'inherit' });
      
      if (fs.existsSync(path.join(pageOutputDir, 'console.json'))) {
        const consoleLog = JSON.parse(fs.readFileSync(path.join(pageOutputDir, 'console.json'), 'utf8'));
        const errors = consoleLog.filter(msg => msg.type === 'error');
        
        if (errors.length > 0) {
          hasErrors = true;
          summary.push({ page: page.name, status: 'failed', errors });
        } else {
          summary.push({ page: page.name, status: 'passed' });
        }
      } else {
        summary.push({ page: page.name, status: 'completed', note: 'No console log generated' });
      }
    } catch (error) {
      hasErrors = true;
      summary.push({ page: page.name, status: 'failed', error: 'Page analysis failed to run.' });
    }
  }

  // Generate combined summary
  const combinedSummary = {
    timestamp: new Date().toISOString(),
    testConfig: config,
    serverHealth: {
      frontend: testSettings ? await checkServerHealth(testSettings.waitForServer.frontend) : 'not_checked',
      backend: testSettings ? await checkServerHealth(testSettings.waitForServer.backend) : 'not_checked'
    },
    pageAnalysis: summary,
    overallStatus: hasErrors ? 'failed' : 'passed'
  };

  fs.writeFileSync(path.join(outputDir, 'summary.json'), JSON.stringify(combinedSummary, null, 2));

  // Create CI/CD summary for GitHub Actions
  const ciSummary = {
    success: !hasErrors,
    total: testResults.length,
    passed: testResults.filter(r => r.result === 'passed').length,
    failed: testResults.filter(r => r.result === 'failed').length,
    duration: performance.now() - startTime,
    failures: testResults.filter(r => r.result === 'failed').map(r => r.test),
    timestamp: new Date().toISOString()
  };
  
  fs.writeFileSync(path.join(outputDir, 'test_summary.json'), JSON.stringify(ciSummary, null, 2));

  console.log(`\n📊 Test run complete. Summary written to ${path.join(outputDir, 'summary.json')}`);
  console.log(`📁 All results saved to: ${outputDir}/`);
  
  if (fs.existsSync(path.join(outputDir, 'test_report.html'))) {
    console.log(`📄 HTML Report: ${outputDir}/test_report.html`);
  }

  // Print CI/CD summary
  console.log('\n📋 CI/CD Summary:');
  console.log(`   Status: ${ciSummary.success ? '✅ PASSED' : '❌ FAILED'}`);
  console.log(`   Tests: ${ciSummary.passed}/${ciSummary.total} passed`);
  console.log(`   Duration: ${Math.round(ciSummary.duration)}ms`);
  
  if (ciSummary.failed > 0) {
    console.log(`   Failed: ${ciSummary.failures.join(', ')}`);
  }

  if (hasErrors) {
    console.error('\n❌ Errors were found during the test run.');
    process.exit(1);
  } else {
    console.log('\n✅ All tests completed successfully.');
    process.exit(0);
  }
}

main().catch(error => {
  console.error('Test runner failed:', error);
  process.exit(1);
});
