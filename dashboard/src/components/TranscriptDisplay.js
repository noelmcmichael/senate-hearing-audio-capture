import React from 'react';
import { FileText, Clock, Volume2 } from 'lucide-react';

const TranscriptDisplay = ({ hearing }) => {
  const hasTranscript = hearing.has_transcript || hearing.full_text_content;
  const transcriptText = hearing.full_text_content;
  
  if (!hasTranscript) {
    return (
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px',
        marginTop: '20px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '10px'
        }}>
          <FileText size={20} color="#888" />
          <h3 style={{ color: '#888', margin: 0 }}>Transcript</h3>
        </div>
        <p style={{ color: '#888', margin: 0 }}>
          No transcript available. Complete the transcription process to view the transcript.
        </p>
      </div>
    );
  }
  
  return (
    <div style={{
      backgroundColor: '#2A2B32',
      border: '1px solid #444',
      borderRadius: '8px',
      padding: '20px',
      marginTop: '20px'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '10px',
        marginBottom: '20px'
      }}>
        <FileText size={20} color="#4ECDC4" />
        <h3 style={{ color: '#FFFFFF', margin: 0 }}>Transcript</h3>
        <div style={{
          backgroundColor: '#4ECDC4',
          color: '#1B1C20',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          fontWeight: 'bold'
        }}>
          AVAILABLE
        </div>
      </div>
      
      {/* Transcript Stats */}
      <div style={{
        display: 'flex',
        gap: '20px',
        marginBottom: '20px',
        padding: '10px',
        backgroundColor: '#1B1C20',
        borderRadius: '6px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Volume2 size={16} color="#888" />
          <span style={{ color: '#888', fontSize: '14px' }}>
            {Math.round(transcriptText.length / 5)} words
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={16} color="#888" />
          <span style={{ color: '#888', fontSize: '14px' }}>
            ~{Math.round(transcriptText.length / 1000)} min read
          </span>
        </div>
      </div>
      
      {/* Transcript Content */}
      <div style={{
        backgroundColor: '#1B1C20',
        border: '1px solid #333',
        borderRadius: '6px',
        padding: '20px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <div style={{
          color: '#FFFFFF',
          lineHeight: '1.6',
          fontSize: '14px',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace'
        }}>
          {transcriptText}
        </div>
      </div>
      
      {/* Actions */}
      <div style={{
        display: 'flex',
        gap: '10px',
        marginTop: '15px'
      }}>
        <button
          onClick={() => {
            navigator.clipboard.writeText(transcriptText);
            alert('Transcript copied to clipboard!');
          }}
          style={{
            backgroundColor: 'transparent',
            color: '#4ECDC4',
            border: '1px solid #4ECDC4',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Copy Text
        </button>
        <button
          onClick={() => {
            const blob = new Blob([transcriptText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `transcript_hearing_${hearing.id}.txt`;
            a.click();
            URL.revokeObjectURL(url);
          }}
          style={{
            backgroundColor: 'transparent',
            color: '#4ECDC4',
            border: '1px solid #4ECDC4',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '14px'
          }}
        >
          Download
        </button>
      </div>
    </div>
  );
};

export default TranscriptDisplay;