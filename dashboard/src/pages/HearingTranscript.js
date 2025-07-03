import React, { useState, useEffect } from 'react';
import { useOutletContext, useNavigate, useParams } from 'react-router-dom';
import { 
  Download, 
  Edit3, 
  Users, 
  Clock, 
  AlertCircle, 
  CheckCircle,
  FileText,
  Play,
  Pause,
  Table,
  BarChart3
} from 'lucide-react';

const HearingTranscript = () => {
  const { hearing, transcript, refreshData } = useOutletContext();
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [selectedSegment, setSelectedSegment] = useState(null);
  const [speakerStats, setSpeakerStats] = useState({});

  useEffect(() => {
    if (transcript?.segments) {
      calculateSpeakerStats();
    }
  }, [transcript]);

  const calculateSpeakerStats = () => {
    if (!transcript?.segments) return;

    const stats = {};
    transcript.segments.forEach(segment => {
      const speaker = segment.speaker || 'UNKNOWN';
      if (!stats[speaker]) {
        stats[speaker] = {
          count: 0,
          totalDuration: 0,
          identified: speaker !== 'UNKNOWN' && speaker !== 'Speaker'
        };
      }
      stats[speaker].count++;
      stats[speaker].totalDuration += (segment.end - segment.start);
    });

    setSpeakerStats(stats);
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatTimestamp = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getSpeakerColor = (speaker) => {
    const colors = {
      'CHAIR': '#4ECDC4',
      'WITNESS': '#FFA500',
      'MEMBER': '#8A2BE2',
      'UNKNOWN': '#FF4444',
      'Speaker': '#FF4444'
    };
    return colors[speaker] || '#888';
  };

  const getSpeakerReviewProgress = () => {
    if (!transcript?.segments) return 0;
    
    const total = transcript.segments.length;
    const identified = transcript.segments.filter(s => 
      s.speaker && s.speaker !== 'UNKNOWN' && s.speaker !== 'Speaker'
    ).length;
    
    return Math.round((identified / total) * 100);
  };

  const handleExportTranscript = () => {
    if (!transcript) return;

    const exportData = {
      hearing_id: hearing.id,
      hearing_title: hearing.hearing_title,
      committee: hearing.committee_code,
      date: hearing.hearing_date,
      transcript: transcript.segments.map(segment => ({
        timestamp: formatTimestamp(segment.start),
        speaker: segment.speaker,
        text: segment.text
      }))
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hearing_${hearing.id}_transcript.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportText = () => {
    if (!transcript) return;

    let textContent = `${hearing.hearing_title}\n`;
    textContent += `Committee: ${hearing.committee_code}\n`;
    textContent += `Date: ${hearing.hearing_date}\n`;
    textContent += `\n${'='.repeat(60)}\n\n`;

    transcript.segments.forEach(segment => {
      textContent += `[${formatTimestamp(segment.start)}] ${segment.speaker}: ${segment.text}\n\n`;
    });

    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hearing_${hearing.id}_transcript.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportCSV = () => {
    if (!transcript) return;

    // CSV header
    let csvContent = 'Hearing ID,Title,Committee,Date,Start Time,End Time,Duration (sec),Speaker,Text\n';
    
    // CSV rows
    transcript.segments.forEach(segment => {
      const duration = segment.end - segment.start;
      const row = [
        hearing.id,
        `"${hearing.hearing_title.replace(/"/g, '""')}"`,
        hearing.committee_code,
        hearing.hearing_date,
        formatTimestamp(segment.start),
        formatTimestamp(segment.end),
        duration,
        segment.speaker,
        `"${segment.text.replace(/"/g, '""')}"`
      ].join(',');
      csvContent += row + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hearing_${hearing.id}_transcript.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportSummaryReport = () => {
    if (!transcript) return;

    const progress = getSpeakerReviewProgress();
    const speakerCounts = {};
    let totalDuration = 0;

    transcript.segments.forEach(segment => {
      const speaker = segment.speaker || 'UNKNOWN';
      const duration = segment.end - segment.start;
      
      if (!speakerCounts[speaker]) {
        speakerCounts[speaker] = { count: 0, duration: 0 };
      }
      speakerCounts[speaker].count++;
      speakerCounts[speaker].duration += duration;
      totalDuration += duration;
    });

    let reportContent = `HEARING TRANSCRIPT ANALYSIS REPORT\n`;
    reportContent += `${'='.repeat(50)}\n\n`;
    reportContent += `Hearing: ${hearing.hearing_title}\n`;
    reportContent += `Committee: ${hearing.committee_code}\n`;
    reportContent += `Date: ${hearing.hearing_date}\n`;
    reportContent += `Total Duration: ${formatTimestamp(totalDuration)}\n`;
    reportContent += `Total Segments: ${transcript.segments.length}\n`;
    reportContent += `Speaker Review Progress: ${progress}%\n\n`;
    
    reportContent += `SPEAKER BREAKDOWN:\n`;
    reportContent += `${'='.repeat(30)}\n`;
    Object.entries(speakerCounts).forEach(([speaker, data]) => {
      const percentage = ((data.duration / totalDuration) * 100).toFixed(1);
      reportContent += `${speaker}: ${data.count} segments, ${formatTimestamp(data.duration)} (${percentage}%)\n`;
    });

    reportContent += `\n\nGENERATED: ${new Date().toLocaleString()}\n`;

    const blob = new Blob([reportContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `hearing_${hearing.id}_analysis_report.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

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

  if (!transcript) {
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
          <FileText size={48} color="#888" style={{ marginBottom: '20px' }} />
          <h3 style={{ color: '#FFFFFF', margin: '0 0 16px 0' }}>
            No Transcript Available
          </h3>
          <p style={{ color: '#888', margin: '0 0 24px 0', lineHeight: '1.6' }}>
            This hearing has not been transcribed yet. Check the Status tab to see the current pipeline progress.
          </p>
          <button
            onClick={() => navigate(`/hearings/${id}/status`)}
            style={{
              backgroundColor: '#4ECDC4',
              color: '#1B1C20',
              border: 'none',
              padding: '12px 24px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '16px',
              fontWeight: 'bold'
            }}
          >
            View Status
          </button>
        </div>
      </div>
    );
  }

  const reviewProgress = getSpeakerReviewProgress();
  const speakerCount = Object.keys(speakerStats).length;
  const unknownSpeakers = speakerStats['UNKNOWN']?.count || 0;

  return (
    <div>
      {/* Transcript Header */}
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px',
        marginBottom: '20px'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: '16px'
        }}>
          <div>
            <h2 style={{ color: '#FFFFFF', margin: '0 0 8px 0', fontSize: '20px' }}>
              Transcript
            </h2>
            <div style={{ color: '#888', fontSize: '14px' }}>
              {transcript.segments?.length || 0} segments • 
              Confidence: {Math.round((transcript.confidence || 0) * 100)}%
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => navigate(`/hearings/${id}/review`)}
              style={{
                backgroundColor: reviewProgress < 100 ? '#FFA500' : '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: 'bold',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Edit3 size={16} />
              {reviewProgress < 100 ? 'Review Speakers' : 'Edit Speakers'}
            </button>
            
            <div style={{ 
              display: 'flex', 
              gap: '8px',
              backgroundColor: '#1B1C20',
              padding: '4px',
              borderRadius: '8px',
              border: '1px solid #444'
            }}>
              <button
                onClick={handleExportTranscript}
                style={{
                  backgroundColor: 'transparent',
                  color: '#4ECDC4',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Download size={14} />
                JSON
              </button>
              
              <button
                onClick={handleExportText}
                style={{
                  backgroundColor: 'transparent',
                  color: '#4ECDC4',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <FileText size={14} />
                Text
              </button>
              
              <button
                onClick={handleExportCSV}
                style={{
                  backgroundColor: 'transparent',
                  color: '#4ECDC4',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <Table size={14} />
                CSV
              </button>
              
              <button
                onClick={handleExportSummaryReport}
                style={{
                  backgroundColor: 'transparent',
                  color: '#4ECDC4',
                  border: 'none',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <BarChart3 size={14} />
                Report
              </button>
            </div>
          </div>
        </div>

        {/* Speaker Review Progress */}
        <div style={{
          backgroundColor: '#1B1C20',
          borderRadius: '6px',
          padding: '16px',
          marginBottom: '16px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '8px'
          }}>
            <span style={{ color: '#4ECDC4', fontSize: '14px', fontWeight: 'bold' }}>
              Speaker Review Progress
            </span>
            <span style={{ color: '#FFFFFF', fontSize: '14px' }}>
              {reviewProgress}% Complete
            </span>
          </div>
          
          <div style={{
            backgroundColor: '#444',
            borderRadius: '4px',
            height: '8px',
            overflow: 'hidden'
          }}>
            <div style={{
              backgroundColor: reviewProgress === 100 ? '#00FF00' : '#4ECDC4',
              height: '100%',
              width: `${reviewProgress}%`,
              transition: 'width 0.3s ease'
            }} />
          </div>
          
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginTop: '8px',
            fontSize: '12px',
            color: '#888'
          }}>
            <span>{speakerCount} speakers identified</span>
            {unknownSpeakers > 0 && (
              <span style={{ color: '#FFA500' }}>
                {unknownSpeakers} unknown speakers
              </span>
            )}
          </div>
        </div>

        {/* Speaker Summary */}
        <div style={{ 
          display: 'flex', 
          gap: '16px', 
          flexWrap: 'wrap',
          fontSize: '14px'
        }}>
          {Object.entries(speakerStats).map(([speaker, stats]) => (
            <div
              key={speaker}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                backgroundColor: '#1B1C20',
                padding: '8px 12px',
                borderRadius: '4px',
                border: `1px solid ${getSpeakerColor(speaker)}`
              }}
            >
              <div style={{
                width: '12px',
                height: '12px',
                borderRadius: '50%',
                backgroundColor: getSpeakerColor(speaker)
              }} />
              <span style={{ color: '#FFFFFF' }}>{speaker}</span>
              <span style={{ color: '#888' }}>({stats.count})</span>
              {!stats.identified && (
                <AlertCircle size={14} color="#FFA500" />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Transcript Content */}
      <div style={{
        backgroundColor: '#2A2B32',
        border: '1px solid #444',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <div style={{ marginBottom: '16px' }}>
          <h3 style={{ color: '#FFFFFF', margin: '0 0 8px 0', fontSize: '18px' }}>
            Full Transcript
          </h3>
          <p style={{ color: '#888', margin: '0', fontSize: '14px' }}>
            Read-only transcript. Use "Review Speakers" to edit speaker assignments.
          </p>
        </div>

        <div style={{ 
          maxHeight: '600px', 
          overflowY: 'auto',
          backgroundColor: '#1B1C20',
          borderRadius: '6px',
          padding: '20px'
        }}>
          {transcript.segments.map((segment, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                gap: '16px',
                marginBottom: '16px',
                padding: '12px',
                backgroundColor: selectedSegment === index ? '#2A2B32' : 'transparent',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'background-color 0.2s ease'
              }}
              onClick={() => setSelectedSegment(selectedSegment === index ? null : index)}
            >
              {/* Timestamp */}
              <div style={{
                minWidth: '80px',
                color: '#888',
                fontSize: '12px',
                fontFamily: 'monospace',
                paddingTop: '2px'
              }}>
                {formatTimestamp(segment.start)}
              </div>

              {/* Speaker */}
              <div style={{
                minWidth: '100px',
                maxWidth: '100px'
              }}>
                <span style={{
                  backgroundColor: getSpeakerColor(segment.speaker),
                  color: segment.speaker === 'UNKNOWN' || segment.speaker === 'Speaker' ? '#FFFFFF' : '#1B1C20',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  display: 'inline-block'
                }}>
                  {segment.speaker}
                </span>
              </div>

              {/* Text */}
              <div style={{
                flex: 1,
                color: '#FFFFFF',
                fontSize: '14px',
                lineHeight: '1.5'
              }}>
                {segment.text}
              </div>

              {/* Duration */}
              <div style={{
                minWidth: '50px',
                color: '#888',
                fontSize: '12px',
                fontFamily: 'monospace',
                paddingTop: '2px',
                textAlign: 'right'
              }}>
                {formatDuration(segment.end - segment.start)}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default HearingTranscript;