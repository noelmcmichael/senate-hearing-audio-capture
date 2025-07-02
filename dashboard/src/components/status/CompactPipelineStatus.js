import React, { useState, useEffect } from 'react';
import { 
  Eye, 
  Search, 
  PlayCircle, 
  MessageSquare, 
  CheckCircle, 
  Zap,
  Activity,
  Clock
} from 'lucide-react';

const CompactPipelineStatus = ({ stage, status, showLabel = true, size = 16 }) => {
  const getStageInfo = (stage) => {
    const stageConfig = {
      'discovered': {
        icon: Eye,
        label: 'Discovered',
        color: '#FFA500',
        bgColor: '#FFA50020'
      },
      'analyzed': {
        icon: Search,
        label: 'Analyzed',
        color: '#4169E1',
        bgColor: '#4169E120'
      },
      'captured': {
        icon: PlayCircle,
        label: 'Captured',
        color: '#32CD32',
        bgColor: '#32CD3220'
      },
      'transcribed': {
        icon: MessageSquare,
        label: 'Transcribed',
        color: '#8A2BE2',
        bgColor: '#8A2BE220'
      },
      'reviewed': {
        icon: CheckCircle,
        label: 'Reviewed',
        color: '#00CED1',
        bgColor: '#00CED120'
      },
      'published': {
        icon: Zap,
        label: 'Published',
        color: '#00FF00',
        bgColor: '#00FF0020'
      }
    };

    return stageConfig[stage] || {
      icon: Clock,
      label: 'Unknown',
      color: '#888',
      bgColor: '#88888820'
    };
  };

  const stageInfo = getStageInfo(stage);
  const isProcessing = status === 'processing';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      padding: '4px 8px',
      backgroundColor: stageInfo.bgColor,
      borderRadius: '12px',
      border: `1px solid ${stageInfo.color}40`
    }}>
      <div style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center'
      }}>
        <stageInfo.icon 
          size={size} 
          color={stageInfo.color}
        />
        {isProcessing && (
          <Activity 
            size={size * 0.6} 
            color="#FFA500"
            style={{
              position: 'absolute',
              top: '-2px',
              right: '-2px',
              animation: 'pulse 1.5s infinite'
            }}
          />
        )}
      </div>
      
      {showLabel && (
        <span style={{
          color: stageInfo.color,
          fontSize: '12px',
          fontWeight: '500'
        }}>
          {stageInfo.label}
          {isProcessing && (
            <span style={{ 
              color: '#FFA500',
              marginLeft: '4px' 
            }}>
              ...
            </span>
          )}
        </span>
      )}

      <style jsx>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  );
};

export default CompactPipelineStatus;