/**
 * StatusWorkflow Component for Phase 7C Milestone 2
 * Visual workflow diagram showing hearing progression through stages
 */

import React from 'react';
import './StatusWorkflow.css';

const StatusWorkflow = ({ 
    currentStatus = 'new', 
    currentStage = 'discovered', 
    compact = false,
    interactive = false,
    onStageClick = null 
}) => {
    
    // Workflow stages with their associated statuses
    const workflowStages = [
        {
            status: 'new',
            stage: 'discovered',
            icon: '🔍',
            label: 'Discovered',
            description: 'Hearing found and catalogued'
        },
        {
            status: 'queued', 
            stage: 'analyzed',
            icon: '🧐',
            label: 'Analyzed',
            description: 'Content analyzed and validated'
        },
        {
            status: 'processing',
            stage: 'captured',
            icon: '🎥',
            label: 'Captured',
            description: 'Audio/video captured'
        },
        {
            status: 'processing',
            stage: 'transcribed',
            icon: '📝',
            label: 'Transcribed',
            description: 'Content transcribed to text'
        },
        {
            status: 'review',
            stage: 'reviewed',
            icon: '✏️',
            label: 'Reviewed',
            description: 'Human review completed'
        },
        {
            status: 'complete',
            stage: 'published',
            icon: '📢',
            label: 'Published',
            description: 'Ready for consumption'
        }
    ];

    // Get current stage index
    const getCurrentStageIndex = () => {
        return workflowStages.findIndex(ws => 
            ws.status === currentStatus && ws.stage === currentStage
        );
    };

    const currentStageIndex = getCurrentStageIndex();

    // Handle stage click
    const handleStageClick = (stage, index) => {
        if (interactive && onStageClick) {
            onStageClick(stage, index);
        }
    };

    // Get stage state (completed, current, upcoming)
    const getStageState = (index) => {
        if (index < currentStageIndex) return 'completed';
        if (index === currentStageIndex) return 'current';
        return 'upcoming';
    };

    if (compact) {
        // Compact horizontal progress bar
        return (
            <div className="status-workflow-compact">
                <div className="workflow-progress-bar">
                    <div 
                        className="workflow-progress-fill"
                        style={{ 
                            width: `${((currentStageIndex + 1) / workflowStages.length) * 100}%` 
                        }}
                    />
                </div>
                <div className="workflow-compact-info">
                    <span className="current-stage-icon">
                        {currentStageIndex >= 0 ? workflowStages[currentStageIndex].icon : '🔍'}
                    </span>
                    <span className="current-stage-label">
                        {currentStageIndex >= 0 ? workflowStages[currentStageIndex].label : 'Discovered'}
                    </span>
                    <span className="stage-progress">
                        {Math.max(0, currentStageIndex + 1)} / {workflowStages.length}
                    </span>
                </div>
            </div>
        );
    }

    // Full workflow diagram
    return (
        <div className="status-workflow">
            <div className="workflow-header">
                <h4>Hearing Workflow Progress</h4>
                <div className="workflow-legend">
                    <div className="legend-item">
                        <div className="legend-dot completed"></div>
                        <span>Completed</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot current"></div>
                        <span>Current</span>
                    </div>
                    <div className="legend-item">
                        <div className="legend-dot upcoming"></div>
                        <span>Upcoming</span>
                    </div>
                </div>
            </div>
            
            <div className="workflow-stages">
                {workflowStages.map((stage, index) => {
                    const state = getStageState(index);
                    
                    return (
                        <div key={`${stage.status}-${stage.stage}`} className="workflow-stage-container">
                            <div 
                                className={`
                                    workflow-stage 
                                    stage-${state}
                                    ${interactive ? 'stage-interactive' : ''}
                                `}
                                onClick={() => handleStageClick(stage, index)}
                            >
                                <div className="stage-indicator">
                                    <div className="stage-icon">{stage.icon}</div>
                                    {state === 'completed' && (
                                        <div className="stage-checkmark">✓</div>
                                    )}
                                    {state === 'current' && (
                                        <div className="stage-pulse"></div>
                                    )}
                                </div>
                                
                                <div className="stage-content">
                                    <h5 className="stage-title">{stage.label}</h5>
                                    <p className="stage-description">{stage.description}</p>
                                    <div className="stage-meta">
                                        Status: <span className="status-badge">{stage.status}</span>
                                    </div>
                                </div>
                            </div>
                            
                            {index < workflowStages.length - 1 && (
                                <div className={`workflow-connector connector-${
                                    index < currentStageIndex ? 'completed' : 'upcoming'
                                }`}>
                                    <div className="connector-line"></div>
                                    <div className="connector-arrow">→</div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default StatusWorkflow;