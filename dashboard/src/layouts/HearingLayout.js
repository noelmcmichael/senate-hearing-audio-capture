import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate, Outlet } from 'react-router-dom';
import { 
  ArrowLeft, 
  FileText, 
  Settings, 
  BarChart3, 
  Volume2,
  CheckCircle,
  AlertCircle,
  Clock
} from 'lucide-react';
import config from '../config';

const HearingLayout = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  
  const [hearing, setHearing] = useState(null);
  const [transcript, setTranscript] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHearingData();
  }, [id]);

  const fetchHearingData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch hearing details
      const hearingResponse = await fetch(`${config.apiUrl}/hearings/${id}`);
      if (!hearingResponse.ok) {
        throw new Error(`Failed to fetch hearing: ${hearingResponse.status}`);
      }
      const hearingData = await hearingResponse.json();
      setHearing(hearingData.hearing || hearingData);

      // Fetch transcript if available
      try {
        const transcriptResponse = await fetch(`${config.apiUrl}/transcript-browser/hearings`);
        if (transcriptResponse.ok) {
          const transcriptData = await transcriptResponse.json();
          const hearingTranscript = transcriptData.transcripts.find(
            t => t.hearing_id === parseInt(id)
          );
          setTranscript(hearingTranscript || null);
        }
      } catch (transcriptError) {
        console.warn('Failed to fetch transcript:', transcriptError);
        setTranscript(null);
      }

    } catch (error) {
      console.error('Error fetching hearing data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getActiveTab = () => {
    if (location.pathname.includes('/review')) return 'review';
    if (location.pathname.includes('/status')) return 'status';
    if (location.pathname.includes('/audio')) return 'audio';
    return 'transcript';
  };

  const handleNavigation = (tab) => {
    const basePath = `/hearings/${id}`;
    switch (tab) {
      case 'transcript':
        navigate(basePath);
        break;
      case 'review':
        navigate(`${basePath}/review`);
        break;
      case 'status':
        navigate(`${basePath}/status`);
        break;
      case 'audio':
        navigate(`${basePath}/audio`);
        break;
      default:
        navigate(basePath);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'No date';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getStatusIcon = (stage) => {
    switch (stage) {
      case 'published':
        return <CheckCircle size={16} color="#00FF00" />;
      case 'reviewed':
      case 'transcribed':
        return <Clock size={16} color="#FFA500" />;
      default:
        return <AlertCircle size={16} color="#888" />;
    }
  };

  const getSpeakerReviewStatus = () => {
    if (!transcript?.segments) return { status: 'no_transcript', text: 'No transcript' };
    
    const segments = transcript.segments;
    const unknownSpeakers = segments.filter(s => 
      s.speaker === 'UNKNOWN' || s.speaker === 'Speaker' || !s.speaker
    ).length;
    
    if (unknownSpeakers === 0) {
      return { status: 'complete', text: 'Speaker review complete' };
    }
    
    if (unknownSpeakers < segments.length / 2) {
      return { status: 'partial', text: `${segments.length - unknownSpeakers}/${segments.length} speakers identified` };
    }
    
    return { status: 'needs_review', text: 'Needs speaker review' };
  };

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        {/* Skeleton Header */}
        <div style={{
          backgroundColor: '#2A2B32',
          borderBottom: '1px solid #444',
          padding: '20px'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '20px',
            marginBottom: '20px'
          }}>
            <div style={{
              width: '24px',
              height: '24px',
              backgroundColor: '#444',
              borderRadius: '4px'
            }} />
            <div style={{
              width: '300px',
              height: '24px',
              backgroundColor: '#444',
              borderRadius: '4px'
            }} />
          </div>
          
          {/* Skeleton Tabs */}
          <div style={{ display: 'flex', gap: '20px' }}>
            {[1, 2, 3, 4].map(i => (
              <div key={i} style={{
                width: '80px',
                height: '32px',
                backgroundColor: '#444',
                borderRadius: '4px'
              }} />
            ))}
          </div>
        </div>
        
        {/* Skeleton Content */}
        <div style={{ padding: '20px' }}>
          <div style={{
            backgroundColor: '#2A2B32',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '20px',
            marginBottom: '20px'
          }}>
            <div style={{
              width: '200px',
              height: '20px',
              backgroundColor: '#444',
              borderRadius: '4px',
              marginBottom: '10px'
            }} />
            <div style={{
              width: '150px',
              height: '16px',
              backgroundColor: '#444',
              borderRadius: '4px'
            }} />
          </div>
          
          {/* Skeleton table rows */}
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} style={{
              backgroundColor: '#2A2B32',
              border: '1px solid #444',
              borderRadius: '8px',
              padding: '15px',
              marginBottom: '10px'
            }}>
              <div style={{
                width: '100%',
                height: '16px',
                backgroundColor: '#444',
                borderRadius: '4px'
              }} />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#1B1C20',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        gap: '20px'
      }}>
        <div style={{ color: '#FF4444', fontSize: '18px' }}>Error: {error}</div>
        <button
          onClick={() => navigate('/')}
          style={{
            backgroundColor: '#4ECDC4',
            color: '#1B1C20',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  if (!hearing) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#1B1C20',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{ color: '#888', fontSize: '18px' }}>Hearing not found</div>
      </div>
    );
  }

  const activeTab = getActiveTab();
  const speakerReviewStatus = getSpeakerReviewStatus();

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
      {/* Header */}
      <div style={{
        backgroundColor: '#2A2B32',
        borderBottom: '1px solid #444',
        padding: '20px'
      }}>
        {/* Back Button */}
        <button
          onClick={() => navigate('/')}
          style={{
            backgroundColor: 'transparent',
            color: '#4ECDC4',
            border: '1px solid #4ECDC4',
            padding: '8px 16px',
            borderRadius: '6px',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '20px'
          }}
        >
          <ArrowLeft size={16} />
          Back to Dashboard
        </button>

        {/* Hearing Info */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '8px' }}>
            <span style={{
              backgroundColor: '#4ECDC4',
              color: '#1B1C20',
              padding: '4px 12px',
              borderRadius: '4px',
              fontSize: '14px',
              fontWeight: 'bold'
            }}>
              {hearing.committee_code}
            </span>
            <span style={{ color: '#888', fontSize: '14px' }}>
              {formatDate(hearing.hearing_date)}
            </span>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {getStatusIcon(hearing.processing_stage)}
              <span style={{ color: '#888', fontSize: '14px' }}>
                {hearing.processing_stage}
              </span>
            </div>
          </div>
          
          <h1 style={{
            color: '#FFFFFF',
            margin: '0 0 8px 0',
            fontSize: '24px',
            lineHeight: '1.3'
          }}>
            {hearing.hearing_title}
          </h1>
          
          <div style={{ color: '#888', fontSize: '14px' }}>
            {hearing.hearing_type} • {speakerReviewStatus.text}
          </div>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '4px' }}>
          {/* Transcript Tab */}
          <button
            onClick={() => handleNavigation('transcript')}
            disabled={!transcript}
            style={{
              backgroundColor: activeTab === 'transcript' ? '#4ECDC4' : 'transparent',
              color: activeTab === 'transcript' ? '#1B1C20' : (transcript ? '#FFFFFF' : '#666'),
              border: `1px solid ${activeTab === 'transcript' ? '#4ECDC4' : '#444'}`,
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: transcript ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px'
            }}
          >
            <FileText size={16} />
            Transcript
            {transcript && (
              <span style={{
                backgroundColor: activeTab === 'transcript' ? '#1B1C20' : '#4ECDC4',
                color: activeTab === 'transcript' ? '#4ECDC4' : '#1B1C20',
                padding: '2px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 'bold'
              }}>
                {transcript.segments?.length || 0}
              </span>
            )}
          </button>

          {/* Review Tab */}
          <button
            onClick={() => handleNavigation('review')}
            disabled={!transcript}
            style={{
              backgroundColor: activeTab === 'review' ? '#4ECDC4' : 'transparent',
              color: activeTab === 'review' ? '#1B1C20' : (transcript ? '#FFFFFF' : '#666'),
              border: `1px solid ${activeTab === 'review' ? '#4ECDC4' : '#444'}`,
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: transcript ? 'pointer' : 'not-allowed',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px'
            }}
          >
            <Settings size={16} />
            Speaker Review
            {transcript && speakerReviewStatus.status !== 'complete' && (
              <span style={{
                backgroundColor: '#FFA500',
                color: '#1B1C20',
                padding: '2px 6px',
                borderRadius: '10px',
                fontSize: '10px',
                fontWeight: 'bold'
              }}>
                !
              </span>
            )}
          </button>

          {/* Status Tab */}
          <button
            onClick={() => handleNavigation('status')}
            style={{
              backgroundColor: activeTab === 'status' ? '#4ECDC4' : 'transparent',
              color: activeTab === 'status' ? '#1B1C20' : '#FFFFFF',
              border: `1px solid ${activeTab === 'status' ? '#4ECDC4' : '#444'}`,
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px'
            }}
          >
            <BarChart3 size={16} />
            Status
          </button>

          {/* Audio Tab */}
          <button
            onClick={() => handleNavigation('audio')}
            style={{
              backgroundColor: activeTab === 'audio' ? '#4ECDC4' : 'transparent',
              color: activeTab === 'audio' ? '#1B1C20' : '#FFFFFF',
              border: `1px solid ${activeTab === 'audio' ? '#4ECDC4' : '#444'}`,
              padding: '10px 16px',
              borderRadius: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px'
            }}
          >
            <Volume2 size={16} />
            Audio
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ padding: '20px' }}>
        <Outlet context={{ hearing, transcript, refreshData: fetchHearingData }} />
      </div>
    </div>
  );
};

export default HearingLayout;