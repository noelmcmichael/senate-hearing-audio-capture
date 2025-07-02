import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, CheckCircle, Clock, HardDrive, Zap, TrendingUp, FileText, MessageSquare, Calendar, Shield, AlertTriangle, Building } from 'lucide-react';
import TranscriptViewer from './components/TranscriptViewer/TranscriptViewer';
import TranscriptBrowser from './components/transcripts/TranscriptBrowser';
import HearingQueue from './components/hearings/HearingQueue';
import HearingDetailsModal from './components/hearings/HearingDetailsModal';
import SystemHealth from './components/monitoring/SystemHealth';
import CommitteeList from './components/committees/CommitteeList';
import CommitteeDetail from './components/committees/CommitteeDetail';

const TranscriptList = ({ onViewTranscript }) => {
  const [transcripts, setTranscripts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTranscripts();
  }, []);

  const fetchTranscripts = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/transcripts');
      if (response.ok) {
        const data = await response.json();
        setTranscripts(data.transcripts || []);
      } else {
        // Mock data for development
        setTranscripts([
          {
            file_path: "output/demo_transcription/senate_hearing_20250627_123720_stream1_complete_transcript.json",
            filename: "senate_hearing_20250627_123720_stream1_complete_transcript.json",
            hearing_id: "DEMO-HEARING",
            segments_count: 150,
            has_corrections: false,
            created: Date.now() / 1000
          }
        ]);
      }
    } catch (error) {
      console.error('Error fetching transcripts:', error);
      // Mock data fallback
      setTranscripts([
        {
          file_path: "output/demo_transcription/senate_hearing_20250627_123720_stream1_complete_transcript.json",
          filename: "senate_hearing_20250627_123720_stream1_complete_transcript.json",
          hearing_id: "DEMO-HEARING",
          segments_count: 150,
          has_corrections: false,
          created: Date.now() / 1000
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div style={{ color: '#888', padding: '20px' }}>Loading transcripts...</div>;
  }

  if (transcripts.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '40px', 
        color: '#888',
        border: '2px dashed #444',
        borderRadius: '8px'
      }}>
        No transcripts available for review yet.
        <br />
        <small>Run the transcription pipeline to generate transcripts.</small>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gap: '12px' }}>
      {transcripts.map((transcript, index) => (
        <div
          key={index}
          style={{
            background: '#2A2B2F',
            border: '1px solid #444',
            borderRadius: '8px',
            padding: '16px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}
        >
          <div>
            <div style={{ 
              fontWeight: '500', 
              color: '#FFFFFF', 
              marginBottom: '4px' 
            }}>
              {transcript.hearing_id}
            </div>
            <div style={{ 
              fontSize: '14px', 
              color: '#888',
              marginBottom: '4px'
            }}>
              {transcript.segments_count} segments
              {transcript.has_corrections && (
                <span style={{ 
                  marginLeft: '8px',
                  background: '#27ae60',
                  color: '#FFFFFF',
                  padding: '2px 6px',
                  borderRadius: '3px',
                  fontSize: '12px'
                }}>
                  Has corrections
                </span>
              )}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {new Date(transcript.created * 1000).toLocaleString()}
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              onClick={() => onViewTranscript(transcript.filename)}
              style={{
                background: '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <MessageSquare size={16} />
              Review
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};

const App = () => {
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard', 'review', 'hearings', 'health', 'committees', 'committee-detail', 'transcripts'
  const [selectedTranscript, setSelectedTranscript] = useState(null);
  const [selectedCommittee, setSelectedCommittee] = useState(null);
  const [selectedHearing, setSelectedHearing] = useState(null);
  const [showHearingDetails, setShowHearingDetails] = useState(false);

  const handleViewTranscript = (transcriptId) => {
    setSelectedTranscript(transcriptId);
    setCurrentView('review');
  };

  const handleBackToDashboard = () => {
    setCurrentView('dashboard');
    setSelectedTranscript(null);
    setSelectedCommittee(null);
  };

  const handleNavigateToHearings = () => {
    setCurrentView('hearings');
  };

  const handleNavigateToHealth = () => {
    setCurrentView('health');
  };

  const handleNavigateToCommittees = () => {
    setCurrentView('committees');
  };

  const handleSelectCommittee = (committee) => {
    setSelectedCommittee(committee);
    setCurrentView('committee-detail');
  };

  const handleViewTranscriptBrowser = () => {
    setCurrentView('transcripts');
  };

  const handleViewTranscriptFromBrowser = (transcript) => {
    setSelectedTranscript(transcript);
    setCurrentView('review');
  };

  const handleBackToCommittees = () => {
    setCurrentView('committees');
    setSelectedCommittee(null);
  };

  const handleViewHearingDetails = async (hearingId) => {
    console.log('View details clicked for hearing ID:', hearingId);
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}`);
      if (response.ok) {
        const hearingDetails = await response.json();
        console.log('Hearing details fetched:', hearingDetails);
        setSelectedHearing(hearingDetails);
        setShowHearingDetails(true);
      } else {
        const errorData = await response.json();
        console.error('API error response:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch hearing details`);
      }
    } catch (error) {
      console.error('Error fetching hearing details:', error);
      alert(`Error loading hearing details: ${error.message}`);
    }
  };

  const handleCloseHearingDetails = () => {
    setShowHearingDetails(false);
    setSelectedHearing(null);
  };

  const handleTriggerCapture = async (hearingId) => {
    try {
      const response = await fetch(`http://localhost:8001/api/hearings/${hearingId}/capture?user_id=ui_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hearing_id: String(hearingId),
          priority: 1,
          capture_options: {
            quality: 'high',
            format: 'wav'
          }
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        alert(`Capture initiated!\n\nHearing: ${result.hearing_title}\nCapture ID: ${result.capture_id}\nStatus: ${result.status}\n\nProcessing will begin shortly...`);
        // Refresh the hearing queue to show updated status
        window.location.reload();
      } else {
        const errorData = await response.json();
        let errorMessage = 'Failed to trigger capture';
        
        if (errorData.detail) {
          if (Array.isArray(errorData.detail)) {
            // Handle Pydantic validation errors
            errorMessage = errorData.detail.map(err => `${err.loc.join('.')}: ${err.msg}`).join('\n');
          } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
          } else {
            errorMessage = JSON.stringify(errorData.detail);
          }
        }
        
        throw new Error(errorMessage);
      }
    } catch (error) {
      console.error('Error triggering capture:', error);
      alert(`Error starting capture: ${error.message}`);
    }
  };

  const handleResolveAlert = (alertId) => {
    console.log('Resolve alert:', alertId);
    // TODO: Implement alert resolution
  };

  // Navigation Header Component
  const NavigationHeader = ({ title, icon, onBack }) => (
    <div style={{ 
      padding: '20px',
      borderBottom: '1px solid #333',
      display: 'flex',
      alignItems: 'center',
      gap: '16px',
      backgroundColor: '#2A2B2F'
    }}>
      <button
        onClick={onBack}
        style={{
          background: '#4ECDC4',
          color: '#1B1C20',
          border: 'none',
          padding: '8px 16px',
          borderRadius: '4px',
          cursor: 'pointer',
          fontWeight: '500'
        }}
      >
        ← Back to Dashboard
      </button>
      <h1 style={{ color: '#FFFFFF', margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
        {icon}
        {title}
      </h1>
    </div>
  );

  // Route to different views
  if (currentView === 'review' && selectedTranscript) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <NavigationHeader 
          title="Transcript Review" 
          icon={<MessageSquare size={24} />}
          onBack={handleBackToDashboard}
        />
        <TranscriptViewer transcriptId={selectedTranscript} />
      </div>
    );
  }

  if (currentView === 'hearings') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <NavigationHeader 
          title="Hearing Queue Management" 
          icon={<Calendar size={24} />}
          onBack={handleBackToDashboard}
        />
        <HearingQueue 
          onViewDetails={handleViewHearingDetails}
          onTriggerCapture={handleTriggerCapture}
        />
      </div>
    );
  }

  if (currentView === 'health') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <NavigationHeader 
          title="System Health Monitor" 
          icon={<Shield size={24} />}
          onBack={handleBackToDashboard}
        />
        <SystemHealth 
          onResolveAlert={handleResolveAlert}
          onViewDetails={handleViewHearingDetails}
        />
      </div>
    );
  }

  if (currentView === 'committees') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <NavigationHeader 
          title="Committee Browser" 
          icon={<Building size={24} />}
          onBack={handleBackToDashboard}
        />
        <CommitteeList onSelectCommittee={handleSelectCommittee} />
      </div>
    );
  }

  if (currentView === 'committee-detail' && selectedCommittee) {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <CommitteeDetail 
          committee={selectedCommittee}
          onBack={handleBackToCommittees}
          onViewDetails={handleViewHearingDetails}
        />
      </div>
    );
  }

  if (currentView === 'transcripts') {
    return (
      <div style={{ minHeight: '100vh', backgroundColor: '#1B1C20' }}>
        <TranscriptBrowser 
          onViewTranscript={handleViewTranscriptFromBrowser}
          onBack={handleBackToDashboard}
        />
      </div>
    );
  }

  return (
    <>
      <Dashboard 
        onViewTranscript={handleViewTranscript} 
        onNavigateToHearings={handleNavigateToHearings}
        onNavigateToHealth={handleNavigateToHealth}
        onNavigateToCommittees={handleNavigateToCommittees}
        onNavigateToTranscripts={handleViewTranscriptBrowser}
      />
      
      {/* Hearing Details Modal */}
      <HearingDetailsModal
        hearing={selectedHearing}
        isOpen={showHearingDetails}
        onClose={handleCloseHearingDetails}
      />
    </>
  );
};

const Dashboard = ({ onViewTranscript, onNavigateToHearings, onNavigateToHealth, onNavigateToCommittees, onNavigateToTranscripts }) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchDashboardData = async () => {
    try {
      // For development, use mock data if API not available
      const mockData = {
        summary: {
          total_extractions: 5,
          successful_extractions: 5,
          success_rate: 100.0,
          total_duration_hours: 8.2,
          total_size_gb: 0.85,
          avg_compression_ratio: 86.3
        },
        committee_stats: {
          'Commerce': 5,
          'Banking': 2,
          'Judiciary': 3,
          'Intelligence': 1
        },
        committee_coverage: {
          total_committees: 10,
          isvp_compatible: 4,
          active_committees: 4,
          coverage_percentage: 40.0
        },
        recent_extractions: [
          {
            timestamp: '20250627_144654',
            hearing_name: 'Finding Nemo S Future Conflicts Over Ocean Resources',
            committee: 'Commerce',
            duration_minutes: 110.6,
            file_size_mb: 151.9,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_144128',
            hearing_name: 'On The Right Track Modernizing Americas Rail Network',
            committee: 'Commerce',
            duration_minutes: 101.9,
            file_size_mb: 139.9,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_202000',
            hearing_name: 'Executive Business Meeting',
            committee: 'Judiciary',
            duration_minutes: 45.2,
            file_size_mb: 62.1,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_201500',
            hearing_name: 'Semiannual Monetary Policy Report',
            committee: 'Banking',
            duration_minutes: 87.3,
            file_size_mb: 119.8,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_201000',
            hearing_name: 'Worldwide Threats Assessment',
            committee: 'Intelligence',
            duration_minutes: 132.1,
            file_size_mb: 181.4,
            format: 'mp3',
            success: true
          },
          {
            timestamp: '20250627_143443',
            hearing_name: 'Executive Session 12',
            committee: 'Commerce',
            duration_minutes: 46.9,
            file_size_mb: 64.5,
            format: 'mp3',
            success: true
          }
        ],
        last_updated: new Date().toISOString()
      };

      setData(mockData);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp || timestamp === 'unknown') return 'Unknown';
    
    const year = timestamp.substring(0, 4);
    const month = timestamp.substring(4, 6);
    const day = timestamp.substring(6, 8);
    const hour = timestamp.substring(9, 11);
    const minute = timestamp.substring(11, 13);
    
    return `${month}/${day}/${year} ${hour}:${minute}`;
  };

  const formatDuration = (minutes) => {
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  if (loading) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <Activity size={48} style={{ color: '#10b981', marginBottom: '1rem' }} />
          <h2>Loading Dashboard...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container">
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <h2 style={{ color: '#ef4444' }}>Error Loading Dashboard</h2>
          <p>{error}</p>
        </div>
      </div>
    );
  }

  const { summary, committee_stats, committee_coverage, recent_extractions } = data;

  // Prepare chart data
  const committeeChartData = Object.entries(committee_stats).map(([name, count]) => ({
    name,
    extractions: count
  }));

  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444'];

  return (
    <div className="container">
      <div className="header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h1>🏛️ Senate Hearing Audio Capture</h1>
            <p>Phase 7B Enhanced UI with automated hearing discovery and management</p>
          </div>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button
              onClick={onNavigateToCommittees}
              style={{
                background: '#8b5cf6',
                color: '#FFFFFF',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Building size={18} />
              Committees
            </button>
            <button
              onClick={onNavigateToHearings}
              style={{
                background: '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Calendar size={18} />
              Hearing Queue
            </button>
            <button
              onClick={onNavigateToTranscripts}
              style={{
                background: '#8b5cf6',
                color: '#FFFFFF',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <FileText size={18} />
              Transcripts
            </button>
            <button
              onClick={onNavigateToHealth}
              style={{
                background: '#3b82f6',
                color: '#FFFFFF',
                border: 'none',
                padding: '12px 16px',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Shield size={18} />
              System Health
            </button>
          </div>
        </div>
        <p style={{ fontSize: '0.9rem', color: '#64748b', margin: 0 }}>
          Last updated: {new Date(data.last_updated).toLocaleString()}
        </p>
      </div>

      {/* Summary Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-value">{summary.total_extractions}</div>
          <div className="stat-label">
            <Activity size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Total Extractions
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#10b981' }}>{summary.success_rate}%</div>
          <div className="stat-label">
            <CheckCircle size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Success Rate
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary.total_duration_hours}h</div>
          <div className="stat-label">
            <Clock size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Total Audio
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{summary.total_size_gb} GB</div>
          <div className="stat-label">
            <HardDrive size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Storage Used
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-value" style={{ color: '#a78bfa' }}>{summary.avg_compression_ratio}%</div>
          <div className="stat-label">
            <Zap size={16} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Compression
          </div>
        </div>
      </div>

      {/* Committee Coverage Section */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>
          🏛️ Multi-Committee Coverage (Phase 1)
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div className="coverage-stat">
            <div className="coverage-value">{committee_coverage.isvp_compatible}</div>
            <div className="coverage-label">ISVP Compatible</div>
          </div>
          <div className="coverage-stat">
            <div className="coverage-value">{committee_coverage.active_committees}</div>
            <div className="coverage-label">Active Committees</div>
          </div>
          <div className="coverage-stat">
            <div className="coverage-value">{committee_coverage.coverage_percentage}%</div>
            <div className="coverage-label">Senate Coverage</div>
          </div>
          <div className="coverage-stat">
            <div className="coverage-value">{committee_coverage.total_committees}</div>
            <div className="coverage-label">Total Committees</div>
          </div>
        </div>
        
        <div style={{ marginTop: '1.5rem' }}>
          <h4 style={{ color: '#10b981', marginBottom: '0.5rem' }}>✅ Supported Committees:</h4>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {Object.keys(committee_stats).map((committee, index) => (
              <span 
                key={committee}
                style={{
                  backgroundColor: COLORS[index % COLORS.length],
                  color: 'white',
                  padding: '0.25rem 0.75rem',
                  borderRadius: '12px',
                  fontSize: '0.875rem',
                  fontWeight: '500'
                }}
              >
                {committee}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>
        <div className="card">
          <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>
            <TrendingUp size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
            Extractions by Committee
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={committeeChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155', 
                  borderRadius: '8px',
                  color: '#e2e8f0'
                }} 
              />
              <Bar dataKey="extractions" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>Committee Distribution</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={committeeChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="extractions"
              >
                {committeeChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1e293b', 
                  border: '1px solid #334155', 
                  borderRadius: '8px',
                  color: '#e2e8f0'
                }} 
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Transcripts Section */}
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>
          <FileText size={20} style={{ display: 'inline', marginRight: '0.5rem' }} />
          Available Transcripts for Review
        </h3>
        <TranscriptList onViewTranscript={onViewTranscript} />
      </div>

      {/* Recent Extractions Table */}
      <div className="card">
        <h3 style={{ margin: '0 0 1rem 0', color: '#f1f5f9' }}>Recent Extractions</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Hearing</th>
              <th>Committee</th>
              <th>Duration</th>
              <th>Size</th>
              <th>Format</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {recent_extractions.map((extraction, index) => (
              <tr key={index}>
                <td className="duration">{formatTimestamp(extraction.timestamp)}</td>
                <td>{extraction.hearing_name}</td>
                <td>
                  <span className="committee-tag">{extraction.committee}</span>
                </td>
                <td className="duration">{formatDuration(extraction.duration_minutes)}</td>
                <td className="file-size">{extraction.file_size_mb} MB</td>
                <td>{extraction.format.toUpperCase()}</td>
                <td>
                  <span className={extraction.success ? 'status-success' : 'status-error'}>
                    {extraction.success ? '✅ Success' : '❌ Failed'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default App;