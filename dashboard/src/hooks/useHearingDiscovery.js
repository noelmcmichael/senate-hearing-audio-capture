import { useState, useEffect, useCallback } from 'react';
import config from '../config';

export const useHearingDiscovery = (selectedCommittees = [], statusFilter = 'all', refreshInterval = 30000) => {
  const [hearings, setHearings] = useState([]);
  const [stats, setStats] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastDiscovery, setLastDiscovery] = useState(null);

  const fetchHearings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const params = new URLSearchParams();
      if (selectedCommittees.length > 0) {
        selectedCommittees.forEach(committee => params.append('committee_codes', committee));
      }
      if (statusFilter !== 'all') {
        params.append('status', statusFilter);
      }
      params.append('limit', '100');

      const response = await fetch(`${config.apiBaseUrl}/api/hearings/discovered?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setHearings(data.data.hearings || []);
      } else {
        throw new Error(data.message || 'Failed to fetch hearings');
      }
    } catch (err) {
      console.error('Error fetching hearings:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [selectedCommittees, statusFilter]);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setStats(data.data);
        setLastDiscovery(data.data.last_discovery);
      }
    } catch (err) {
      console.error('Error fetching stats:', err);
    }
  }, []);

  const discoverHearings = useCallback(async (committeeCodes = []) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/discover`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          committee_codes: committeeCodes.length > 0 ? committeeCodes : null
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setLastDiscovery(data.data.discovery_date);
        // Refresh hearings and stats after discovery
        await fetchHearings();
        await fetchStats();
        return data.data;
      } else {
        throw new Error(data.message || 'Discovery failed');
      }
    } catch (err) {
      console.error('Error running discovery:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchHearings, fetchStats]);

  const refreshHearings = useCallback(async () => {
    await Promise.all([fetchHearings(), fetchStats()]);
  }, [fetchHearings, fetchStats]);

  // Initial load
  useEffect(() => {
    refreshHearings();
  }, [refreshHearings]);

  // Auto-refresh
  useEffect(() => {
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        refreshHearings();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [refreshHearings, refreshInterval]);

  return {
    hearings,
    stats,
    isLoading,
    error,
    discoverHearings,
    refreshHearings,
    lastDiscovery
  };
};