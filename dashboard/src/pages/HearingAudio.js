import React from 'react';
import { useOutletContext } from 'react-router-dom';
import { Volume2, AlertCircle } from 'lucide-react';

const HearingAudio = () => {
  const { hearing, transcript } = useOutletContext();

  if (!hearing) {
    return (
      <div style={{ 
        textAlign: 'center', 
        color: '#888', 
        padding: '60px 20px',
        fontSize: '18px'
      }}>
        Loading hearing data...
      </div>
    );
  }

  return (
    <div style={{ 
      textAlign: 'center', 
      padding: '60px 20px'
    }}>
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '40px',
        maxWidth: '500px',
        margin: '0 auto'
      }}>
        <Volume2 size={48} color="#888" style={{ marginBottom: '20px' }} />
        <h3 style={{ color: '#FFFFFF', margin: '0 0 16px 0' }}>
          Audio Player Coming Soon
        </h3>
        <p style={{ color: '#888', margin: '0', lineHeight: '1.6' }}>
          Audio playback and synchronization features will be implemented in a future update.
        </p>
      </div>
    </div>
  );
};

export default HearingAudio;