import React, { useState } from 'react';
import { Users, Check, X } from 'lucide-react';

const BulkOperations = ({ 
  selectedCount, 
  speakerOptions, 
  onBulkAssign, 
  selectedSegments,
  onClearSelection 
}) => {
  const [selectedSpeaker, setSelectedSpeaker] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);

  const handleBulkAssign = async () => {
    if (!selectedSpeaker || selectedSegments.size === 0) return;
    
    setIsAssigning(true);
    try {
      await onBulkAssign(selectedSegments, selectedSpeaker);
      setSelectedSpeaker('');
    } catch (error) {
      console.error('Error in bulk assignment:', error);
    } finally {
      setIsAssigning(false);
    }
  };

  return (
    <div className="bulk-operations">
      <div className="bulk-header">
        <div className="selection-info">
          <Users size={20} />
          <span className="selection-count">
            {selectedCount} segment{selectedCount !== 1 ? 's' : ''} selected
          </span>
        </div>
        
        <button 
          onClick={onClearSelection}
          className="clear-selection-button"
          title="Clear selection"
        >
          <X size={16} />
          Clear
        </button>
      </div>

      <div className="bulk-assignment">
        <div className="assignment-controls">
          <div className="speaker-select-group">
            <label htmlFor="bulk-speaker-select">Assign all to:</label>
            <select
              id="bulk-speaker-select"
              value={selectedSpeaker}
              onChange={(e) => setSelectedSpeaker(e.target.value)}
              className="bulk-speaker-select"
            >
              <option value="">Select speaker...</option>
              {speakerOptions.map((speaker) => (
                <option key={speaker} value={speaker}>
                  {speaker}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleBulkAssign}
            disabled={!selectedSpeaker || isAssigning || selectedSegments.size === 0}
            className="bulk-assign-button"
          >
            {isAssigning ? (
              <>
                <div className="loading-spinner" />
                Assigning...
              </>
            ) : (
              <>
                <Check size={16} />
                Assign {selectedCount}
              </>
            )}
          </button>
        </div>

        <div className="bulk-info">
          <div className="info-text">
            This will assign "{selectedSpeaker || 'selected speaker'}" to all {selectedCount} selected segments.
          </div>
        </div>
      </div>

      <style jsx>{`
        .bulk-operations {
          position: sticky;
          top: 20px;
          background: linear-gradient(135deg, #f39c12, #e67e22);
          color: #1B1C20;
          border-radius: 8px;
          padding: 16px;
          margin-bottom: 20px;
          box-shadow: 0 4px 12px rgba(243, 156, 18, 0.3);
          z-index: 10;
        }

        .bulk-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .selection-info {
          display: flex;
          align-items: center;
          gap: 8px;
          font-weight: 600;
          font-size: 16px;
        }

        .selection-count {
          color: #1B1C20;
        }

        .clear-selection-button {
          background: rgba(27, 28, 32, 0.1);
          color: #1B1C20;
          border: 1px solid rgba(27, 28, 32, 0.2);
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 14px;
          transition: all 0.2s ease;
        }

        .clear-selection-button:hover {
          background: rgba(27, 28, 32, 0.2);
        }

        .bulk-assignment {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .assignment-controls {
          display: flex;
          gap: 12px;
          align-items: flex-end;
        }

        .speaker-select-group {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .speaker-select-group label {
          font-size: 14px;
          font-weight: 500;
          color: #1B1C20;
        }

        .bulk-speaker-select {
          background: #FFFFFF;
          color: #1B1C20;
          border: 1px solid rgba(27, 28, 32, 0.2);
          padding: 8px 12px;
          border-radius: 4px;
          font-size: 14px;
          min-width: 200px;
        }

        .bulk-speaker-select:focus {
          outline: none;
          border-color: #1B1C20;
          box-shadow: 0 0 0 2px rgba(27, 28, 32, 0.1);
        }

        .bulk-assign-button {
          background: #27ae60;
          color: #FFFFFF;
          border: none;
          padding: 8px 16px;
          border-radius: 4px;
          cursor: pointer;
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 14px;
          font-weight: 500;
          transition: all 0.2s ease;
          white-space: nowrap;
        }

        .bulk-assign-button:hover:not(:disabled) {
          background: #219a52;
          transform: translateY(-1px);
        }

        .bulk-assign-button:disabled {
          background: #95a5a6;
          cursor: not-allowed;
          transform: none;
        }

        .loading-spinner {
          width: 16px;
          height: 16px;
          border: 2px solid transparent;
          border-top: 2px solid #FFFFFF;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .bulk-info {
          padding: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
        }

        .info-text {
          font-size: 12px;
          color: #1B1C20;
          opacity: 0.8;
        }

        @media (max-width: 768px) {
          .bulk-operations {
            position: relative;
            top: auto;
          }

          .bulk-header {
            flex-direction: column;
            gap: 8px;
            align-items: stretch;
          }

          .assignment-controls {
            flex-direction: column;
            gap: 8px;
          }

          .bulk-speaker-select {
            min-width: auto;
          }

          .selection-info {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
};

export default BulkOperations;