#!/usr/bin/env node

/**
 * Performance Alert System
 * 
 * Monitors performance metrics and sends alerts when thresholds are exceeded
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class PerformanceAlerts {
  constructor() {
    this.resultsDir = 'playwright-results';
    this.configFile = path.join(this.resultsDir, 'performance_config.json');
    this.alertsFile = path.join(this.resultsDir, 'performance_alerts.json');
    
    // Default configuration
    this.defaultConfig = {
      alertThresholds: {
        dashboardLoad: 12000,        // Alert if > 12 seconds
        hearingPageLoad: 8000,       // Alert if > 8 seconds
        searchResponse: 1500,        // Alert if > 1.5 seconds
        filterResponse: 800,         // Alert if > 800ms
        regressionPercent: 15,       // Alert if > 15% regression
        consecutiveFailures: 2       // Alert after 2 consecutive failures
      },
      notifications: {
        console: true,
        file: true,
        email: false,                // Can be enabled with email config
        slack: false                 // Can be enabled with webhook
      },
      emailConfig: {
        // Add email configuration if needed
        enabled: false,
        to: [],
        subject: 'Performance Alert: Senate Hearing System'
      },
      slackConfig: {
        // Add Slack webhook if needed
        enabled: false,
        webhook: null,
        channel: '#performance-alerts'
      }
    };
  }

  loadConfig() {
    if (fs.existsSync(this.configFile)) {
      return JSON.parse(fs.readFileSync(this.configFile, 'utf8'));
    }
    
    // Create default config
    this.saveConfig(this.defaultConfig);
    return this.defaultConfig;
  }

  saveConfig(config) {
    if (!fs.existsSync(this.resultsDir)) {
      fs.mkdirSync(this.resultsDir, { recursive: true });
    }
    fs.writeFileSync(this.configFile, JSON.stringify(config, null, 2));
  }

  loadAlertHistory() {
    if (fs.existsSync(this.alertsFile)) {
      return JSON.parse(fs.readFileSync(this.alertsFile, 'utf8'));
    }
    return [];
  }

  saveAlertHistory(alerts) {
    fs.writeFileSync(this.alertsFile, JSON.stringify(alerts, null, 2));
  }

  async checkPerformanceResults() {
    const resultsFile = path.join(this.resultsDir, 'performance_results.json');
    
    if (!fs.existsSync(resultsFile)) {
      console.log('⚠️  No performance results found');
      return;
    }
    
    const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
    const config = this.loadConfig();
    const alertHistory = this.loadAlertHistory();
    
    const newAlerts = [];
    
    console.log('🔍 Analyzing performance results for alerts...');
    
    // Check each test result
    results.tests.forEach(test => {
      const alerts = this.analyzeTest(test, config.alertThresholds);
      newAlerts.push(...alerts);
    });
    
    // Check for existing regression alerts
    if (results.alerts && results.alerts.length > 0) {
      results.alerts.forEach(alert => {
        newAlerts.push({
          type: 'regression',
          test: alert.test,
          message: `Performance regression detected: ${alert.test}`,
          details: {
            baseline: alert.baseline,
            current: alert.current,
            increase: alert.increase,
            percentageIncrease: alert.percentageIncrease
          },
          severity: alert.percentageIncrease > 30 ? 'high' : 'medium',
          timestamp: new Date().toISOString()
        });
      });
    }
    
    // Add new alerts to history
    alertHistory.push(...newAlerts);
    
    // Keep only last 100 alerts
    if (alertHistory.length > 100) {
      alertHistory.splice(0, alertHistory.length - 100);
    }
    
    this.saveAlertHistory(alertHistory);
    
    // Send notifications
    if (newAlerts.length > 0) {
      await this.sendNotifications(newAlerts, config.notifications);
    }
    
    return newAlerts;
  }

  analyzeTest(test, thresholds) {
    const alerts = [];
    
    // Check load time thresholds
    if (test.name === 'Dashboard Load' && test.loadTime > thresholds.dashboardLoad) {
      alerts.push({
        type: 'threshold_exceeded',
        test: test.name,
        metric: 'loadTime',
        value: test.loadTime,
        threshold: thresholds.dashboardLoad,
        message: `Dashboard load time ${Math.round(test.loadTime)}ms exceeds threshold ${thresholds.dashboardLoad}ms`,
        severity: test.loadTime > thresholds.dashboardLoad * 1.5 ? 'high' : 'medium',
        timestamp: new Date().toISOString()
      });
    }
    
    if (test.name === 'Hearing Page Load' && test.loadTime > thresholds.hearingPageLoad) {
      alerts.push({
        type: 'threshold_exceeded',
        test: test.name,
        metric: 'loadTime',
        value: test.loadTime,
        threshold: thresholds.hearingPageLoad,
        message: `Hearing page load time ${Math.round(test.loadTime)}ms exceeds threshold ${thresholds.hearingPageLoad}ms`,
        severity: test.loadTime > thresholds.hearingPageLoad * 1.5 ? 'high' : 'medium',
        timestamp: new Date().toISOString()
      });
    }
    
    // Check interaction performance
    if (test.name === 'Interaction Performance') {
      if (test.searchTime > thresholds.searchResponse) {
        alerts.push({
          type: 'threshold_exceeded',
          test: test.name,
          metric: 'searchTime',
          value: test.searchTime,
          threshold: thresholds.searchResponse,
          message: `Search response time ${Math.round(test.searchTime)}ms exceeds threshold ${thresholds.searchResponse}ms`,
          severity: 'medium',
          timestamp: new Date().toISOString()
        });
      }
      
      if (test.filterTime > thresholds.filterResponse) {
        alerts.push({
          type: 'threshold_exceeded',
          test: test.name,
          metric: 'filterTime',
          value: test.filterTime,
          threshold: thresholds.filterResponse,
          message: `Filter response time ${Math.round(test.filterTime)}ms exceeds threshold ${thresholds.filterResponse}ms`,
          severity: 'medium',
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Check Web Vitals
    if (test.webVitals) {
      if (test.webVitals.fcp > 3000) {
        alerts.push({
          type: 'web_vital_threshold',
          test: test.name,
          metric: 'First Contentful Paint',
          value: test.webVitals.fcp,
          threshold: 3000,
          message: `First Contentful Paint ${Math.round(test.webVitals.fcp)}ms exceeds threshold 3000ms`,
          severity: 'medium',
          timestamp: new Date().toISOString()
        });
      }
      
      if (test.webVitals.lcp > 2500) {
        alerts.push({
          type: 'web_vital_threshold',
          test: test.name,
          metric: 'Largest Contentful Paint',
          value: test.webVitals.lcp,
          threshold: 2500,
          message: `Largest Contentful Paint ${Math.round(test.webVitals.lcp)}ms exceeds threshold 2500ms`,
          severity: 'high',
          timestamp: new Date().toISOString()
        });
      }
      
      if (test.webVitals.cls > 0.1) {
        alerts.push({
          type: 'web_vital_threshold',
          test: test.name,
          metric: 'Cumulative Layout Shift',
          value: test.webVitals.cls,
          threshold: 0.1,
          message: `Cumulative Layout Shift ${test.webVitals.cls.toFixed(3)} exceeds threshold 0.1`,
          severity: 'high',
          timestamp: new Date().toISOString()
        });
      }
    }
    
    // Check test failures
    if (!test.passed) {
      alerts.push({
        type: 'test_failure',
        test: test.name,
        message: `Performance test failed: ${test.name}`,
        details: {
          errors: test.errors || [],
          warnings: test.warnings || []
        },
        severity: 'high',
        timestamp: new Date().toISOString()
      });
    }
    
    return alerts;
  }

  async sendNotifications(alerts, notificationConfig) {
    console.log(`\n🚨 ${alerts.length} Performance Alert(s) Detected!`);
    
    // Console notification
    if (notificationConfig.console) {
      console.log('\n📋 Alert Details:');
      alerts.forEach(alert => {
        const severityIcon = alert.severity === 'high' ? '🔴' : '🟠';
        console.log(`${severityIcon} ${alert.message}`);
        
        if (alert.details) {
          console.log(`   Details: ${JSON.stringify(alert.details, null, 2)}`);
        }
      });
    }
    
    // File notification
    if (notificationConfig.file) {
      const notificationFile = path.join(this.resultsDir, 'performance_notifications.log');
      const logEntry = `\n[${new Date().toISOString()}] Performance Alerts:\n${alerts.map(a => `- ${a.message}`).join('\n')}\n`;
      fs.appendFileSync(notificationFile, logEntry);
      console.log(`📝 Alerts logged to: ${notificationFile}`);
    }
    
    // Email notification (if configured)
    if (notificationConfig.email && notificationConfig.email.enabled) {
      await this.sendEmailAlert(alerts, notificationConfig.email);
    }
    
    // Slack notification (if configured)
    if (notificationConfig.slack && notificationConfig.slack.enabled) {
      await this.sendSlackAlert(alerts, notificationConfig.slack);
    }
  }

  async sendEmailAlert(alerts, emailConfig) {
    console.log('📧 Email notifications not implemented yet');
    // TODO: Implement email notifications
  }

  async sendSlackAlert(alerts, slackConfig) {
    console.log('📱 Slack notifications not implemented yet');
    // TODO: Implement Slack notifications
  }

  generateAlertSummary() {
    const alertHistory = this.loadAlertHistory();
    const recentAlerts = alertHistory.filter(alert => {
      const alertDate = new Date(alert.timestamp);
      const dayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
      return alertDate > dayAgo;
    });
    
    const summary = {
      total: alertHistory.length,
      recent: recentAlerts.length,
      byType: {},
      bySeverity: {},
      byTest: {}
    };
    
    alertHistory.forEach(alert => {
      summary.byType[alert.type] = (summary.byType[alert.type] || 0) + 1;
      summary.bySeverity[alert.severity] = (summary.bySeverity[alert.severity] || 0) + 1;
      summary.byTest[alert.test] = (summary.byTest[alert.test] || 0) + 1;
    });
    
    return summary;
  }

  async generateAlertReport() {
    const summary = this.generateAlertSummary();
    const alertHistory = this.loadAlertHistory();
    
    const reportPath = path.join(this.resultsDir, 'performance_alert_report.html');
    
    const html = `
<!DOCTYPE html>
<html>
<head>
    <title>Performance Alert Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #dc3545; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric { background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }
        .alert { margin-bottom: 15px; padding: 15px; border-radius: 8px; }
        .alert.high { background: #f8d7da; border: 1px solid #f5c6cb; }
        .alert.medium { background: #fff3cd; border: 1px solid #ffeaa7; }
        .alert.low { background: #d1ecf1; border: 1px solid #bee5eb; }
        .alert-time { font-size: 12px; color: #666; }
        .chart { background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Performance Alert Report</h1>
            <p>Senate Hearing Transcription System - Performance Monitoring Alerts</p>
            <p>Generated: ${new Date().toLocaleString()}</p>
        </div>
        
        <div class="summary">
            <div class="metric">
                <h3>${summary.total}</h3>
                <p>Total Alerts</p>
            </div>
            <div class="metric">
                <h3>${summary.recent}</h3>
                <p>Recent (24h)</p>
            </div>
            <div class="metric">
                <h3>${summary.bySeverity.high || 0}</h3>
                <p>High Severity</p>
            </div>
            <div class="metric">
                <h3>${summary.bySeverity.medium || 0}</h3>
                <p>Medium Severity</p>
            </div>
        </div>
        
        <h2>Alert Breakdown</h2>
        <div class="chart">
            <h3>By Type</h3>
            ${Object.entries(summary.byType).map(([type, count]) => `
                <p>${type}: ${count}</p>
            `).join('')}
        </div>
        
        <div class="chart">
            <h3>By Test</h3>
            ${Object.entries(summary.byTest).map(([test, count]) => `
                <p>${test}: ${count}</p>
            `).join('')}
        </div>
        
        <h2>Recent Alerts</h2>
        ${alertHistory.slice(-20).reverse().map(alert => `
            <div class="alert ${alert.severity}">
                <strong>${alert.message}</strong>
                <div class="alert-time">${new Date(alert.timestamp).toLocaleString()}</div>
                ${alert.details ? `<pre>${JSON.stringify(alert.details, null, 2)}</pre>` : ''}
            </div>
        `).join('')}
    </div>
</body>
</html>
    `;
    
    fs.writeFileSync(reportPath, html);
    console.log(`✅ Alert report generated: ${reportPath}`);
  }
}

// CLI Interface
async function main() {
  const alerts = new PerformanceAlerts();
  
  const command = process.argv[2];
  
  switch (command) {
    case 'check':
      await alerts.checkPerformanceResults();
      break;
      
    case 'report':
      await alerts.generateAlertReport();
      break;
      
    case 'summary':
      const summary = alerts.generateAlertSummary();
      console.log('📊 Performance Alert Summary:');
      console.log(JSON.stringify(summary, null, 2));
      break;
      
    case 'config':
      const config = alerts.loadConfig();
      console.log('⚙️  Performance Alert Configuration:');
      console.log(JSON.stringify(config, null, 2));
      break;
      
    default:
      console.log('📋 Performance Alert System Usage:');
      console.log('  node performance-alerts.js check   - Check latest results for alerts');
      console.log('  node performance-alerts.js report  - Generate alert report');
      console.log('  node performance-alerts.js summary - Show alert summary');
      console.log('  node performance-alerts.js config  - Show configuration');
  }
}

if (require.main === module) {
  main().catch(error => {
    console.error('Performance alert system failed:', error);
    process.exit(1);
  });
}

module.exports = PerformanceAlerts;