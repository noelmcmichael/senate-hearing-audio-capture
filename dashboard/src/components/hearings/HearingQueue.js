import React, { useState, useEffect } from 'react';
import { 
  Calendar, 
  Filter, 
  Clock, 
  PlayCircle, 
  AlertCircle, 
  CheckCircle, 
  Users,
  ExternalLink,
  MoreVertical,
  ChevronDown
} from 'lucide-react';

const HearingQueue = ({ onViewDetails, onTriggerCapture }) => {
  const [hearings, setHearings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    committee_codes: [],
    sync_status: 'all',
    has_streams: 'all',
    date_range: 'week'
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total: 0
  });

  const committees = [
    'SCOM', 'SSCI', 'SBAN', 'SSJU', 'HJUD', 'SSAF', 'SSHR', 'SSBE'
  ];

  const syncStatusOptions = [
    { value: 'all', label: 'All Status' },
    { value: 'synced', label: 'Synced' },
    { value: 'pending_sync', label: 'Pending Sync' },
    { value: 'failed', label: 'Sync Failed' }
  ];

  useEffect(() => {
    fetchHearings();
  }, [filters, pagination.offset]);

  const fetchHearings = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: pagination.limit,
        offset: pagination.offset
      });

      if (filters.committee_codes.length > 0) {
        params.append('committee_codes', filters.committee_codes.join(','));
      }
      
      if (filters.sync_status !== 'all') {
        params.append('sync_status', filters.sync_status);
      }
      
      if (filters.has_streams !== 'all') {
        params.append('has_streams', filters.has_streams === 'true');
      }

      // Add date range filter
      const now = new Date();
      let dateFrom;
      switch (filters.date_range) {
        case 'today':
          dateFrom = new Date(now.getFullYear(), now.getMonth(), now.getDate());
          break;
        case 'week':
          dateFrom = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          break;
        case 'month':
          dateFrom = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          break;
        default:
          dateFrom = null;
      }

      if (dateFrom) {
        params.append('date_from', dateFrom.toISOString().split('T')[0]);
      }

      const response = await fetch(`/api/hearings/queue?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setHearings(data.hearings || []);
      setPagination(prev => ({
        ...prev,
        total: data.pagination?.total || 0
      }));

    } catch (err) {
      console.error('Error fetching hearings:', err);
      setError(err.message);
      
      // Mock data for development
      setHearings([
        {
          id: '1',
          hearing_title: 'Executive Session - Nomination Hearings',
          committee_code: 'SSJU',
          hearing_date: '2025-06-28',
          hearing_type: 'Executive Session',
          sync_status: 'synced',
          has_streams: true,
          streams: { 'isvp': 'http://example.com/stream1' },
          review_priority: 8,
          review_status: 'pending',
          sync_confidence: 0.95,
          capture_readiness: { score: 0.85, recommendation: 'Ready for immediate capture' }
        },
        {
          id: '2',
          hearing_title: 'Oversight of Federal Regulatory Agencies',
          committee_code: 'SCOM',
          hearing_date: '2025-06-27',
          hearing_type: 'Oversight Hearing',
          sync_status: 'synced',
          has_streams: false,
          streams: {},
          review_priority: 5,
          review_status: 'in_progress',
          sync_confidence: 0.78,
          capture_readiness: { score: 0.45, recommendation: 'Not recommended for capture' }
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, offset: 0 })); // Reset to first page
  };

  const handleCommitteeFilter = (committee) => {
    setFilters(prev => ({
      ...prev,
      committee_codes: prev.committee_codes.includes(committee)
        ? prev.committee_codes.filter(c => c !== committee)
        : [...prev.committee_codes, committee]
    }));
  };

  const getSyncStatusColor = (status) => {
    switch (status) {
      case 'synced': return '#10b981';
      case 'pending_sync': return '#f59e0b';
      case 'failed': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getReadinessColor = (score) => {
    if (score >= 0.8) return '#10b981';
    if (score >= 0.6) return '#f59e0b';
    return '#ef4444';
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getPriorityColor = (priority) => {
    if (priority >= 8) return '#ef4444';
    if (priority >= 6) return '#f59e0b';
    if (priority >= 4) return '#3b82f6';
    return '#6b7280';
  };

  if (loading) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#1B1C20',
        color: '#FFFFFF' 
      }}>
        <div style={{ marginBottom: '1rem' }}>
          <Clock size={48} style={{ color: '#4ECDC4' }} />
        </div>
        <h3>Loading Hearing Queue...</h3>
        <p style={{ color: '#888' }}>Fetching synchronized hearings from database</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        padding: '2rem', 
        textAlign: 'center', 
        backgroundColor: '#1B1C20',
        color: '#FFFFFF' 
      }}>
        <div style={{ marginBottom: '1rem' }}>
          <AlertCircle size={48} style={{ color: '#ef4444' }} />
        </div>
        <h3>Error Loading Hearings</h3>
        <p style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</p>
        <button
          onClick={fetchHearings}
          style={{
            backgroundColor: '#4ECDC4',
            color: '#1B1C20',
            border: 'none',
            padding: '8px 16px',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div style={{ backgroundColor: '#1B1C20', color: '#FFFFFF', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ 
        padding: '1.5rem',
        borderBottom: '1px solid #333',
        backgroundColor: '#2A2B2F'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h1 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <Calendar size={28} style={{ color: '#4ECDC4' }} />
            Hearing Queue
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ color: '#888' }}>
              {pagination.total} hearings found
            </span>
            <button
              onClick={fetchHearings}
              style={{
                backgroundColor: '#4ECDC4',
                color: '#1B1C20',
                border: 'none',
                padding: '8px 12px',
                borderRadius: '4px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}
            >
              <Calendar size={16} />
              Refresh
            </button>
          </div>
        </div>

        {/* Filters */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {/* Committee Filter */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#CCCCCC' }}>
              Committees
            </label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {committees.map(committee => (
                <button
                  key={committee}
                  onClick={() => handleCommitteeFilter(committee)}
                  style={{
                    backgroundColor: filters.committee_codes.includes(committee) ? '#4ECDC4' : '#333',
                    color: filters.committee_codes.includes(committee) ? '#1B1C20' : '#FFFFFF',
                    border: '1px solid #444',
                    padding: '4px 8px',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '0.875rem'
                  }}
                >
                  {committee}
                </button>
              ))}
            </div>
          </div>

          {/* Sync Status Filter */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#CCCCCC' }}>
              Sync Status
            </label>
            <select
              value={filters.sync_status}
              onChange={(e) => handleFilterChange('sync_status', e.target.value)}
              style={{
                backgroundColor: '#333',
                color: '#FFFFFF',
                border: '1px solid #444',
                padding: '8px',
                borderRadius: '4px',
                width: '100%'
              }}
            >
              {syncStatusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Stream Availability Filter */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#CCCCCC' }}>
              Stream Availability
            </label>
            <select
              value={filters.has_streams}
              onChange={(e) => handleFilterChange('has_streams', e.target.value)}
              style={{
                backgroundColor: '#333',
                color: '#FFFFFF',
                border: '1px solid #444',
                padding: '8px',
                borderRadius: '4px',
                width: '100%'
              }}
            >
              <option value="all">All Hearings</option>
              <option value="true">Has Streams</option>
              <option value="false">No Streams</option>
            </select>
          </div>

          {/* Date Range Filter */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: '#CCCCCC' }}>
              Date Range
            </label>
            <select
              value={filters.date_range}
              onChange={(e) => handleFilterChange('date_range', e.target.value)}
              style={{
                backgroundColor: '#333',
                color: '#FFFFFF',
                border: '1px solid #444',
                padding: '8px',
                borderRadius: '4px',
                width: '100%'
              }}
            >
              <option value="today">Today</option>
              <option value="week">Past Week</option>
              <option value="month">Past Month</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>
      </div>

      {/* Hearings List */}
      <div style={{ padding: '1.5rem' }}>
        {hearings.length === 0 ? (
          <div style={{ 
            textAlign: 'center', 
            padding: '3rem',
            border: '2px dashed #444',
            borderRadius: '8px'
          }}>
            <Calendar size={48} style={{ color: '#666', marginBottom: '1rem' }} />
            <h3 style={{ color: '#888' }}>No hearings found</h3>
            <p style={{ color: '#666' }}>
              Try adjusting your filters or check back later for new hearings.
            </p>
          </div>
        ) : (
          <div style={{ display: 'grid', gap: '1rem' }}>
            {hearings.map(hearing => (
              <div
                key={hearing.id}
                style={{
                  backgroundColor: '#2A2B2F',
                  border: '1px solid #444',
                  borderRadius: '8px',
                  padding: '1.5rem',
                  position: 'relative'
                }}
              >
                <div style={{ display: 'grid', gridTemplateColumns: '1fr auto', gap: '1rem', alignItems: 'start' }}>
                  {/* Main Content */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                      <h3 style={{ 
                        margin: 0, 
                        color: '#FFFFFF',
                        cursor: 'pointer',
                        textDecoration: 'underline'
                      }}
                      onClick={() => onViewDetails && onViewDetails(hearing.id)}
                      >
                        {hearing.hearing_title}
                      </h3>
                      
                      {/* Priority Badge */}
                      {hearing.review_priority > 0 && (
                        <span style={{
                          backgroundColor: getPriorityColor(hearing.review_priority),
                          color: '#FFFFFF',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '0.75rem',
                          fontWeight: 'bold'
                        }}>
                          P{hearing.review_priority}
                        </span>
                      )}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
                      {/* Committee & Date */}
                      <div>
                        <div style={{ color: '#888', fontSize: '0.875rem' }}>Committee & Date</div>
                        <div style={{ color: '#FFFFFF', fontWeight: '500' }}>
                          {hearing.committee_code} • {formatDate(hearing.hearing_date)}
                        </div>
                      </div>

                      {/* Sync Status */}
                      <div>
                        <div style={{ color: '#888', fontSize: '0.875rem' }}>Sync Status</div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '0.5rem',
                          color: getSyncStatusColor(hearing.sync_status)
                        }}>
                          <div style={{
                            width: '8px',
                            height: '8px',
                            borderRadius: '50%',
                            backgroundColor: getSyncStatusColor(hearing.sync_status)
                          }} />
                          {hearing.sync_status.replace('_', ' ').toUpperCase()}
                          {hearing.sync_confidence && (
                            <span style={{ color: '#888', fontSize: '0.75rem' }}>
                              ({Math.round(hearing.sync_confidence * 100)}%)
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Stream Status */}
                      <div>
                        <div style={{ color: '#888', fontSize: '0.875rem' }}>Streams</div>
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          gap: '0.5rem',
                          color: hearing.has_streams ? '#10b981' : '#ef4444'
                        }}>
                          {hearing.has_streams ? <CheckCircle size={16} /> : <AlertCircle size={16} />}
                          {hearing.has_streams ? `${Object.keys(hearing.streams).length} available` : 'None found'}
                        </div>
                      </div>

                      {/* Review Status */}
                      <div>
                        <div style={{ color: '#888', fontSize: '0.875rem' }}>Review Status</div>
                        <div style={{ color: '#FFFFFF' }}>
                          {hearing.review_status ? hearing.review_status.replace('_', ' ').toUpperCase() : 'Not Started'}
                        </div>
                      </div>
                    </div>

                    {/* Capture Readiness */}
                    {hearing.capture_readiness && (
                      <div style={{ 
                        backgroundColor: '#1B1C20',
                        padding: '0.75rem',
                        borderRadius: '4px',
                        border: `1px solid ${getReadinessColor(hearing.capture_readiness.score)}`
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                          <div style={{
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            backgroundColor: getReadinessColor(hearing.capture_readiness.score)
                          }} />
                          <span style={{ fontWeight: '500', color: '#FFFFFF' }}>
                            Capture Readiness: {Math.round(hearing.capture_readiness.score * 100)}%
                          </span>
                        </div>
                        <div style={{ color: '#888', fontSize: '0.875rem' }}>
                          {hearing.capture_readiness.recommendation}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', minWidth: '120px' }}>
                    {hearing.has_streams && (
                      <button
                        onClick={() => onTriggerCapture && onTriggerCapture(hearing.id)}
                        style={{
                          backgroundColor: '#4ECDC4',
                          color: '#1B1C20',
                          border: 'none',
                          padding: '8px 12px',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          justifyContent: 'center',
                          fontWeight: '500'
                        }}
                      >
                        <PlayCircle size={16} />
                        Capture
                      </button>
                    )}
                    
                    <button
                      onClick={() => onViewDetails && onViewDetails(hearing.id)}
                      style={{
                        backgroundColor: 'transparent',
                        color: '#4ECDC4',
                        border: '1px solid #4ECDC4',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        justifyContent: 'center'
                      }}
                    >
                      <ExternalLink size={16} />
                      Details
                    </button>

                    <button
                      style={{
                        backgroundColor: 'transparent',
                        color: '#888',
                        border: '1px solid #444',
                        padding: '8px 12px',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        justifyContent: 'center'
                      }}
                    >
                      <MoreVertical size={16} />
                      More
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pagination.total > pagination.limit && (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            gap: '1rem',
            marginTop: '2rem',
            padding: '1rem',
            borderTop: '1px solid #333'
          }}>
            <button
              disabled={pagination.offset === 0}
              onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
              style={{
                backgroundColor: pagination.offset === 0 ? '#333' : '#4ECDC4',
                color: pagination.offset === 0 ? '#888' : '#1B1C20',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: pagination.offset === 0 ? 'not-allowed' : 'pointer'
              }}
            >
              Previous
            </button>

            <span style={{ color: '#888' }}>
              {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total}
            </span>

            <button
              disabled={pagination.offset + pagination.limit >= pagination.total}
              onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
              style={{
                backgroundColor: pagination.offset + pagination.limit >= pagination.total ? '#333' : '#4ECDC4',
                color: pagination.offset + pagination.limit >= pagination.total ? '#888' : '#1B1C20',
                border: 'none',
                padding: '8px 16px',
                borderRadius: '4px',
                cursor: pagination.offset + pagination.limit >= pagination.total ? 'not-allowed' : 'pointer'
              }}
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default HearingQueue;