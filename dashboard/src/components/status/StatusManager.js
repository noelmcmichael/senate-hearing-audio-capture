/**
 * StatusManager Component for Phase 7C Milestone 2
 * Modal interface for status changes, reviewer assignment, and bulk operations
 */

import React, { useState, useEffect } from 'react';
import StatusIndicator from './StatusIndicator';
import './StatusManager.css';

const StatusManager = ({ 
    isOpen, 
    onClose, 
    hearingIds = [], 
    currentHearing = null, 
    onStatusUpdate = null,
    bulkMode = false 
}) => {
    
    const [selectedStatus, setSelectedStatus] = useState('');
    const [selectedStage, setSelectedStage] = useState('');
    const [assignedReviewer, setAssignedReviewer] = useState('');
    const [reviewerNotes, setReviewerNotes] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    // Status options
    const statusOptions = [
        'new', 'queued', 'processing', 'review', 'complete', 'error'
    ];

    // Processing stage options
    const stageOptions = [
        'discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published'
    ];

    // Sample reviewers (in production, this would come from an API)
    const reviewerOptions = [
        'reviewer@example.com',
        'senior.reviewer@example.com', 
        'quality.controller@example.com',
        'admin@example.com'
    ];

    // Initialize form with current hearing data
    useEffect(() => {
        if (currentHearing) {
            setSelectedStatus(currentHearing.status || '');
            setSelectedStage(currentHearing.processing_stage || '');
            setAssignedReviewer(currentHearing.assigned_reviewer || '');
            setReviewerNotes(currentHearing.reviewer_notes || '');
        } else {
            // Reset form for bulk operations
            setSelectedStatus('');
            setSelectedStage('');
            setAssignedReviewer('');
            setReviewerNotes('');
        }
        setError('');
    }, [currentHearing, isOpen]);

    // Handle status update
    const handleStatusUpdate = async () => {
        if (!selectedStatus) {
            setError('Please select a status');
            return;
        }

        setIsLoading(true);
        setError('');

        try {
            if (bulkMode) {
                // Bulk update
                const response = await fetch('/api/hearings/bulk-status', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        hearing_ids: hearingIds,
                        status: selectedStatus,
                        processing_stage: selectedStage || undefined,
                        assigned_reviewer: assignedReviewer || undefined,
                        notes: reviewerNotes || undefined
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to update hearings');
                }

                const result = await response.json();
                
                if (onStatusUpdate) {
                    onStatusUpdate(result);
                }

            } else {
                // Single hearing update
                const hearingId = currentHearing?.id;
                if (!hearingId) {
                    throw new Error('No hearing selected');
                }

                const response = await fetch(`/api/hearings/${hearingId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        status: selectedStatus,
                        processing_stage: selectedStage || undefined,
                        reviewer_notes: reviewerNotes || undefined
                    })
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Failed to update hearing');
                }

                const result = await response.json();

                // Also update reviewer if specified
                if (assignedReviewer && assignedReviewer !== currentHearing.assigned_reviewer) {
                    await fetch(`/api/hearings/${hearingId}/reviewer`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            assigned_reviewer: assignedReviewer
                        })
                    });
                }

                if (onStatusUpdate) {
                    onStatusUpdate(result);
                }
            }

            onClose();

        } catch (err) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="status-manager-overlay">
            <div className="status-manager-modal">
                <div className="status-manager-header">
                    <h3>
                        {bulkMode 
                            ? `Update Status for ${hearingIds.length} Hearing${hearingIds.length > 1 ? 's' : ''}`
                            : `Update Hearing Status`
                        }
                    </h3>
                    <button 
                        className="status-manager-close"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        ×
                    </button>
                </div>

                <div className="status-manager-content">
                    {currentHearing && !bulkMode && (
                        <div className="current-hearing-info">
                            <h4>{currentHearing.hearing_title}</h4>
                            <p className="hearing-meta">
                                {currentHearing.committee_code} • {currentHearing.hearing_date}
                            </p>
                            <div className="current-status">
                                <span>Current Status:</span>
                                <StatusIndicator 
                                    status={currentHearing.status}
                                    processing_stage={currentHearing.processing_stage}
                                    showStage={true}
                                />
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="status-manager-error">
                            {error}
                        </div>
                    )}

                    <div className="form-group">
                        <label>Status *</label>
                        <select 
                            value={selectedStatus} 
                            onChange={(e) => setSelectedStatus(e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">Select status...</option>
                            {statusOptions.map(status => (
                                <option key={status} value={status}>
                                    {status.charAt(0).toUpperCase() + status.slice(1)}
                                </option>
                            ))}
                        </select>
                        {selectedStatus && (
                            <div className="status-preview">
                                <StatusIndicator status={selectedStatus} />
                            </div>
                        )}
                    </div>

                    <div className="form-group">
                        <label>Processing Stage</label>
                        <select 
                            value={selectedStage} 
                            onChange={(e) => setSelectedStage(e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">Select stage...</option>
                            {stageOptions.map(stage => (
                                <option key={stage} value={stage}>
                                    {stage.charAt(0).toUpperCase() + stage.slice(1)}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Assigned Reviewer</label>
                        <select 
                            value={assignedReviewer} 
                            onChange={(e) => setAssignedReviewer(e.target.value)}
                            disabled={isLoading}
                        >
                            <option value="">No assignment...</option>
                            {reviewerOptions.map(reviewer => (
                                <option key={reviewer} value={reviewer}>
                                    {reviewer}
                                </option>
                            ))}
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Notes</label>
                        <textarea 
                            value={reviewerNotes}
                            onChange={(e) => setReviewerNotes(e.target.value)}
                            placeholder="Add notes about this status change..."
                            rows={3}
                            disabled={isLoading}
                        />
                    </div>
                </div>

                <div className="status-manager-actions">
                    <button 
                        className="btn-secondary"
                        onClick={onClose}
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    <button 
                        className="btn-primary"
                        onClick={handleStatusUpdate}
                        disabled={isLoading || !selectedStatus}
                    >
                        {isLoading ? 'Updating...' : 'Update Status'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default StatusManager;