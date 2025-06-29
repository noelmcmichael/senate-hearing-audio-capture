import React, { useState, useEffect } from 'react';
import './CommitteeSelector.css';

const CommitteeSelector = ({ onSelect, selectedCommittee, placeholder = "Select Committee" }) => {
  const [committees, setCommittees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetchCommittees();
  }, []);

  const fetchCommittees = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/committees');
      if (response.ok) {
        const data = await response.json();
        setCommittees(data.committees || []);
      }
    } catch (err) {
      console.error('Error fetching committees:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = (committee) => {
    onSelect(committee);
    setIsOpen(false);
  };

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  if (loading) {
    return <div className="committee-selector loading">Loading...</div>;
  }

  return (
    <div className="committee-selector">
      <div className="selector-button" onClick={toggleDropdown}>
        <span className="selected-text">
          {selectedCommittee ? (
            <>
              <span className="committee-code">{selectedCommittee.code}</span>
              {selectedCommittee.name}
            </>
          ) : (
            placeholder
          )}
        </span>
        <span className={`dropdown-arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>

      {isOpen && (
        <div className="dropdown-menu">
          <div className="dropdown-header">
            <span>Select Committee</span>
          </div>
          {committees.map((committee) => (
            <div
              key={committee.code}
              className={`dropdown-item ${selectedCommittee?.code === committee.code ? 'selected' : ''}`}
              onClick={() => handleSelect(committee)}
            >
              <div className="committee-option">
                <span className="committee-code">{committee.code}</span>
                <span className="committee-name">{committee.name}</span>
                <span className="hearing-count">{committee.hearing_count} hearings</span>
              </div>
            </div>
          ))}
          {committees.length === 0 && (
            <div className="dropdown-item disabled">No committees available</div>
          )}
        </div>
      )}
    </div>
  );
};

export default CommitteeSelector;