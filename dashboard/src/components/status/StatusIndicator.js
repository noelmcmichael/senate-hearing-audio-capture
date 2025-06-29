/**
 * StatusIndicator Component for Phase 7C Milestone 2
 * Visual status badges with color coding, icons, and click handlers for status changes
 */

import React from 'react';
import './StatusIndicator.css';

const StatusIndicator = ({ 
    status, 
    processing_stage, 
    size = 'medium', 
    showStage = false, 
    clickable = false, 
    onClick = null,
    tooltip = true 
}) => {
    
    // Status configuration with colors, icons, and descriptions
    const statusConfig = {
        'new': {
            color: '#6b7280', // gray
            bgColor: '#f3f4f6',
            icon: '📝',
            label: 'New',
            description: 'Recently discovered, not yet processed'
        },
        'queued': {
            color: '#3b82f6', // blue  
            bgColor: '#dbeafe',
            icon: '⏳',
            label: 'Queued',
            description: 'Scheduled for processing'
        },
        'processing': {
            color: '#f59e0b', // amber
            bgColor: '#fef3c7',
            icon: '⚙️',
            label: 'Processing',
            description: 'Currently being processed'
        },
        'review': {
            color: '#8b5cf6', // purple
            bgColor: '#ede9fe',
            icon: '👁️',
            label: 'Review',
            description: 'Under human review'
        },
        'complete': {
            color: '#10b981', // green
            bgColor: '#d1fae5',
            icon: '✅',
            label: 'Complete',
            description: 'Processing completed successfully'
        },
        'error': {
            color: '#ef4444', // red
            bgColor: '#fee2e2',
            icon: '❌',
            label: 'Error',
            description: 'Processing failed, requires attention'
        }
    };

    // Processing stage configuration
    const stageConfig = {
        'discovered': { icon: '🔍', label: 'Discovered' },
        'analyzed': { icon: '🧐', label: 'Analyzed' },
        'captured': { icon: '🎥', label: 'Captured' },
        'transcribed': { icon: '📝', label: 'Transcribed' },
        'reviewed': { icon: '✏️', label: 'Reviewed' },
        'published': { icon: '📢', label: 'Published' }
    };

    const config = statusConfig[status] || statusConfig['new'];
    const stageInfo = stageConfig[processing_stage] || stageConfig['discovered'];

    // Size classes
    const sizeClasses = {
        'small': 'status-indicator-small',
        'medium': 'status-indicator-medium', 
        'large': 'status-indicator-large'
    };

    // Handle click
    const handleClick = () => {
        if (clickable && onClick) {
            onClick(status);
        }
    };

    // Build tooltip content
    const tooltipContent = showStage && processing_stage 
        ? `${config.description} - Stage: ${stageInfo.label}`
        : config.description;

    return (
        <div className="status-indicator-container">
            <div 
                className={`
                    status-indicator 
                    ${sizeClasses[size]} 
                    ${clickable ? 'status-indicator-clickable' : ''}
                `}
                style={{
                    backgroundColor: config.bgColor,
                    color: config.color,
                    borderColor: config.color
                }}
                onClick={handleClick}
                title={tooltip ? tooltipContent : ''}
            >
                <span className="status-icon">{config.icon}</span>
                <span className="status-label">{config.label}</span>
                {showStage && processing_stage && (
                    <span className="status-stage">
                        <span className="stage-separator">•</span>
                        <span className="stage-icon">{stageInfo.icon}</span>
                        <span className="stage-label">{stageInfo.label}</span>
                    </span>
                )}
            </div>
        </div>
    );
};

export default StatusIndicator;