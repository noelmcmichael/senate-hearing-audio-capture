import React, { useState, useEffect } from 'react';
import { 
  Eye, 
  Search, 
  PlayCircle, 
  MessageSquare, 
  CheckCircle, 
  Zap,
  Clock,
  RotateCcw,
  Activity
} from 'lucide-react';

const PipelineStatusIndicator = ({ hearingId, refreshInterval = 5000 }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
    
    // Set up polling for real-time updates
    const interval = setInterval(fetchStatus, refreshInterval);
    return () => clearInterval(interval);
  }, [hearingId, refreshInterval]);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}`);
      if (response.ok) {
        const data = await response.json();
        setStatus({
          stage: data.processing_stage,
          status: data.status,
          updated_at: data.updated_at,
          last_check: new Date().toLocaleTimeString()
        });
        setError(null);
      } else {
        console.error('Failed to fetch hearing status');
      }
    } catch (err) {
      setError(err.message);
      console.error('Error fetching hearing status:', err);
    } finally {
      setLoading(false);
    }
  };

  const getStageInfo = (stage) => {
    const stageConfig = {
      'discovered': {
        icon: Eye,
        label: 'Discovered',
        color: '#FFA500',
        description: 'Hearing found and catalogued'
      },
      'analyzed': {
        icon: Search,
        label: 'Analyzed',
        color: '#4169E1',
        description: 'Metadata extracted and validated'
      },
      'captured': {
        icon: PlayCircle,
        label: 'Captured',
        color: '#32CD32',
        description: 'Audio successfully captured'
      },
      'transcribed': {
        icon: MessageSquare,
        label: 'Transcribed',
        color: '#8A2BE2',
        description: 'Audio converted to text'
      },
      'reviewed': {
        icon: CheckCircle,
        label: 'Reviewed',
        color: '#00CED1',
        description: 'Quality review completed'
      },
      'published': {
        icon: Zap,
        label: 'Published',
        color: '#00FF00',
        description: 'Available for public access'
      }
    };

    return stageConfig[stage] || {
      icon: Clock,
      label: 'Unknown',
      color: '#888',
      description: 'Status unknown'
    };
  };

  const getStageIndex = (stage) => {
    const stages = ['discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published'];
    return stages.indexOf(stage);
  };

  const isStageActive = (stageIndex, currentIndex) => {
    return stageIndex <= currentIndex;
  };

  const isStageInProgress = (stageIndex, currentIndex) => {
    return stageIndex === currentIndex && status?.status === 'processing';
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        color: '#888',
        fontSize: '14px'
      }}>
        <RotateCcw size={16} className="animate-spin" />
        Loading status...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        color: '#FF4444',
        fontSize: '14px'
      }}>
        Error loading status: {error}
      </div>
    );
  }

  if (!status) {
    return (
      <div style={{
        color: '#888',
        fontSize: '14px'
      }}>
        No status available
      </div>
    );
  }

  const currentStageInfo = getStageInfo(status.stage);
  const currentIndex = getStageIndex(status.stage);
  const stages = ['discovered', 'analyzed', 'captured', 'transcribed', 'reviewed', 'published'];

  return (
    <div style={{
      backgroundColor: '#1E1F25',
      borderRadius: '8px',
      padding: '12px',
      border: '1px solid #333'
    }}>
      {/* Current Status Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '12px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <currentStageInfo.icon 
            size={16} 
            color={currentStageInfo.color}
          />
          <span style={{
            color: currentStageInfo.color,
            fontSize: '14px',
            fontWeight: 'bold'
          }}>
            {currentStageInfo.label}
          </span>
          {status.status === 'processing' && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              color: '#FFA500'
            }}>
              <Activity size={12} />
              <span style={{ fontSize: '12px' }}>Processing...</span>
            </div>
          )}
        </div>
        <div style={{
          color: '#888',
          fontSize: '11px'
        }}>
          Updated: {status.last_check}
        </div>
      </div>

      {/* Pipeline Progress Bar */}
      <div style={{ marginBottom: '8px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '4px',
          marginBottom: '6px'
        }}>
          {stages.map((stage, index) => {
            const stageInfo = getStageInfo(stage);
            const isActive = isStageActive(index, currentIndex);
            const inProgress = isStageInProgress(index, currentIndex);
            
            return (
              <React.Fragment key={stage}>
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '2px'
                }}>
                  <div style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    backgroundColor: isActive ? stageInfo.color : '#333',
                    border: inProgress ? `2px solid ${stageInfo.color}` : '1px solid #555',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    position: 'relative'
                  }}>
                    <stageInfo.icon 
                      size={12} 
                      color={isActive ? '#FFFFFF' : '#666'} 
                    />
                    {inProgress && (
                      <div style={{
                        position: 'absolute',
                        width: '30px',
                        height: '30px',
                        borderRadius: '50%',
                        border: `2px solid ${stageInfo.color}`,
                        borderTopColor: 'transparent',
                        animation: 'spin 1s linear infinite'
                      }} />
                    )}
                  </div>
                  <span style={{
                    fontSize: '9px',
                    color: isActive ? '#FFFFFF' : '#666',
                    textAlign: 'center',
                    width: '40px'
                  }}>
                    {stageInfo.label}
                  </span>
                </div>
                
                {index < stages.length - 1 && (
                  <div style={{
                    flex: 1,
                    height: '2px',
                    backgroundColor: isActive && index < currentIndex ? stageInfo.color : '#333',
                    margin: '0 4px',
                    minWidth: '20px'
                  }} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Stage Description */}
      <div style={{
        color: '#888',
        fontSize: '12px',
        lineHeight: '1.4'
      }}>
        {currentStageInfo.description}
      </div>

      {/* Add spinning animation CSS */}
      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
};

export default PipelineStatusIndicator;