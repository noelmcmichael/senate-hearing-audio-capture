import { useState, useEffect, useCallback } from 'react';
import config from '../config';

export const useHearingCapture = (refreshInterval = 5000) => {
  const [activeProcesses, setActiveProcesses] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchActiveProcesses = useCallback(async () => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/processing`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        setActiveProcesses(data.data.processes || {});
      } else {
        console.error('Failed to fetch active processes:', data.message);
      }
    } catch (err) {
      console.error('Error fetching active processes:', err);
    }
  }, []);

  const captureHearing = useCallback(async (hearingId, options = {}) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/${hearingId}/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          hearing_id: hearingId,
          options: options
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Start monitoring this hearing
        await fetchActiveProcesses();
        return data.data;
      } else {
        throw new Error(data.detail?.message || data.message || 'Capture failed');
      }
    } catch (err) {
      console.error('Error capturing hearing:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [fetchActiveProcesses]);

  const cancelProcessing = useCallback(async (hearingId) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/${hearingId}/cancel`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Remove from active processes
        setActiveProcesses(prev => {
          const updated = { ...prev };
          delete updated[hearingId];
          return updated;
        });
        return data.data;
      } else {
        throw new Error(data.detail?.message || data.message || 'Cancel failed');
      }
    } catch (err) {
      console.error('Error cancelling processing:', err);
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getProcessingProgress = useCallback(async (hearingId) => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/${hearingId}/progress`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      } else {
        throw new Error(data.message || 'Failed to get progress');
      }
    } catch (err) {
      console.error('Error getting processing progress:', err);
      return null;
    }
  }, []);

  const getHearingDetails = useCallback(async (hearingId) => {
    try {
      const response = await fetch(`${config.apiBaseUrl}/api/hearings/${hearingId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        return data.data;
      } else {
        throw new Error(data.detail?.message || data.message || 'Failed to get hearing details');
      }
    } catch (err) {
      console.error('Error getting hearing details:', err);
      throw err;
    }
  }, []);

  // Auto-refresh active processes
  useEffect(() => {
    fetchActiveProcesses();
    
    if (refreshInterval > 0) {
      const interval = setInterval(() => {
        fetchActiveProcesses();
      }, refreshInterval);

      return () => clearInterval(interval);
    }
  }, [fetchActiveProcesses, refreshInterval]);

  return {
    activeProcesses,
    isLoading,
    error,
    captureHearing,
    cancelProcessing,
    getProcessingProgress,
    getHearingDetails,
    refreshActiveProcesses: fetchActiveProcesses
  };
};