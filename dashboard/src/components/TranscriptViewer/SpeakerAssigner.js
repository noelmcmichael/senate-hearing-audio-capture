import React, { useState } from 'react';
import { User, CheckCircle, AlertCircle } from 'lucide-react';

const SpeakerAssigner = ({ segment, speakerOptions, onAssign }) => {
  const [selectedSpeaker, setSelectedSpeaker] = useState(
    segment.speaker || segment.review_metadata?.correction?.speaker_name || ''
  );
  const [isEditing, setIsEditing] = useState(false);
  const [customSpeaker, setCustomSpeaker] = useState('');

  const currentSpeaker = segment.review_metadata?.correction?.speaker_name || segment.speaker;
  const hasCorrection = segment.review_metadata?.has_correction;
  const needsReview = segment.review_metadata?.needs_review;

  const handleSpeakerSelect = (speakerName) => {
    setSelectedSpeaker(speakerName);
    onAssign(speakerName, 1.0);
    setIsEditing(false);
    setCustomSpeaker('');
  };

  const handleCustomSpeakerSubmit = () => {
    if (customSpeaker.trim()) {
      handleSpeakerSelect(customSpeaker.trim());
    }
  };

  const getStatusIcon = () => {
    if (hasCorrection) {
      return <CheckCircle size={16} className="status-icon corrected" />;
    } else if (needsReview) {
      return <AlertCircle size={16} className="status-icon needs-review" />;
    }
    return <User size={16} className="status-icon reviewed" />;
  };

  const getStatusText = () => {
    if (hasCorrection) return 'Corrected';
    if (needsReview) return 'Needs Review';
    return 'Reviewed';
  };

  return (
    <div className="speaker-assigner">
      <div className="current-assignment">
        <div className="assignment-header">
          {getStatusIcon()}
          <span className="assignment-label">Speaker:</span>
          <span className={`current-speaker ${!currentSpeaker ? 'unknown' : ''}`}>
            {currentSpeaker || 'Unknown Speaker'}
          </span>
          <span className="status-text">{getStatusText()}</span>
        </div>
        
        {!isEditing && (
          <button 
            onClick={() => setIsEditing(true)}
            className="edit-button"
          >
            {currentSpeaker ? 'Change' : 'Assign'}
          </button>
        )}
      </div>

      {isEditing && (
        <div className="speaker-editor">
          <div className="speaker-options">
            <div className="options-header">
              <span>Select Speaker:</span>
              <button 
                onClick={() => setIsEditing(false)}
                className="cancel-button"
              >
                Cancel
              </button>
            </div>
            
            <div className="options-grid">
              {speakerOptions.map((speaker) => (
                <button
                  key={speaker}
                  onClick={() => handleSpeakerSelect(speaker)}
                  className={`speaker-option ${selectedSpeaker === speaker ? 'selected' : ''}`}
                >
                  {speaker}
                </button>
              ))}
            </div>
          </div>

          <div className="custom-speaker">
            <div className="custom-input-group">
              <input
                type="text"
                value={customSpeaker}
                onChange={(e) => setCustomSpeaker(e.target.value)}
                placeholder="Enter custom speaker name..."
                className="custom-speaker-input"
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleCustomSpeakerSubmit();
                  }
                }}
              />
              <button
                onClick={handleCustomSpeakerSubmit}
                disabled={!customSpeaker.trim()}
                className="add-custom-button"
              >
                Add
              </button>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        .speaker-assigner {
          background: #34353A;
          border-radius: 6px;
          padding: 12px;
          border: 1px solid #444;
        }

        .current-assignment {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .assignment-header {
          display: flex;
          align-items: center;
          gap: 8px;
          flex: 1;
        }

        .status-icon {
          flex-shrink: 0;
        }

        .status-icon.corrected {
          color: #27ae60;
        }

        .status-icon.needs-review {
          color: #e74c3c;
        }

        .status-icon.reviewed {
          color: #95a5a6;
        }

        .assignment-label {
          font-weight: 500;
          color: #FFFFFF;
          font-size: 14px;
        }

        .current-speaker {
          font-weight: 600;
          color: #4ECDC4;
          font-size: 14px;
        }

        .current-speaker.unknown {
          color: #e74c3c;
          font-style: italic;
        }

        .status-text {
          font-size: 12px;
          color: #888;
          margin-left: auto;
          margin-right: 8px;
        }

        .edit-button {
          background: #4ECDC4;
          color: #1B1C20;
          border: none;
          padding: 4px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 500;
          transition: background-color 0.2s ease;
        }

        .edit-button:hover {
          background: #45B7B8;
        }

        .speaker-editor {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid #444;
        }

        .speaker-options {
          margin-bottom: 12px;
        }

        .options-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 8px;
        }

        .options-header span {
          font-size: 14px;
          font-weight: 500;
          color: #FFFFFF;
        }

        .cancel-button {
          background: none;
          color: #888;
          border: 1px solid #666;
          padding: 2px 8px;
          border-radius: 3px;
          cursor: pointer;
          font-size: 12px;
        }

        .cancel-button:hover {
          color: #FFFFFF;
          border-color: #888;
        }

        .options-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
          gap: 6px;
          max-height: 200px;
          overflow-y: auto;
        }

        .speaker-option {
          background: #2A2B2F;
          color: #FFFFFF;
          border: 1px solid #666;
          padding: 6px 10px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          text-align: left;
          transition: all 0.2s ease;
        }

        .speaker-option:hover {
          background: #3A3B3F;
          border-color: #4ECDC4;
        }

        .speaker-option.selected {
          background: #4ECDC4;
          color: #1B1C20;
          border-color: #4ECDC4;
        }

        .custom-speaker {
          border-top: 1px solid #444;
          padding-top: 8px;
        }

        .custom-input-group {
          display: flex;
          gap: 8px;
        }

        .custom-speaker-input {
          flex: 1;
          background: #2A2B2F;
          color: #FFFFFF;
          border: 1px solid #666;
          padding: 6px 10px;
          border-radius: 4px;
          font-size: 12px;
        }

        .custom-speaker-input:focus {
          outline: none;
          border-color: #4ECDC4;
        }

        .custom-speaker-input::placeholder {
          color: #888;
        }

        .add-custom-button {
          background: #4ECDC4;
          color: #1B1C20;
          border: none;
          padding: 6px 12px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 12px;
          font-weight: 500;
          transition: background-color 0.2s ease;
        }

        .add-custom-button:hover:not(:disabled) {
          background: #45B7B8;
        }

        .add-custom-button:disabled {
          background: #666;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .current-assignment {
            flex-direction: column;
            align-items: stretch;
            gap: 8px;
          }

          .assignment-header {
            justify-content: center;
          }

          .options-grid {
            grid-template-columns: 1fr;
          }

          .custom-input-group {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  );
};

export default SpeakerAssigner;