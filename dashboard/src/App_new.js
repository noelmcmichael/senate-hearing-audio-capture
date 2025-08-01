import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import HearingLayout from './layouts/HearingLayout';
import HearingTranscript from './pages/HearingTranscript';
import HearingReview from './pages/HearingReview';
import HearingStatus from './pages/HearingStatus';
import HearingAudio from './pages/HearingAudio';
import './App.css';

const App = () => {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Dashboard Route */}
          <Route path="/" element={<Dashboard />} />
          
          {/* Hearing Routes */}
          <Route path="/hearings/:id" element={<HearingLayout />}>
            <Route index element={<HearingTranscript />} />
            <Route path="review" element={<HearingReview />} />
            <Route path="status" element={<HearingStatus />} />
            <Route path="audio" element={<HearingAudio />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
};

export default App;