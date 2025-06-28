import React, { useState, useRef, useImperativeHandle, forwardRef } from 'react';
import { Play, Pause, SkipBack, SkipForward, Volume2 } from 'lucide-react';

const AudioPlayer = forwardRef(({ 
  audioFile, 
  onTimeUpdate, 
  currentSegment, 
  segments 
}, ref) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1.0);
  const [playbackRate, setPlaybackRate] = useState(1.0);
  
  const audioRef = useRef(null);

  // Expose audio ref to parent component
  useImperativeHandle(ref, () => audioRef.current);

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      const time = audioRef.current.currentTime;
      setCurrentTime(time);
      onTimeUpdate?.(time);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const handleSeek = (e) => {
    if (audioRef.current) {
      const rect = e.currentTarget.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const percentage = x / rect.width;
      const newTime = percentage * duration;
      
      audioRef.current.currentTime = newTime;
      setCurrentTime(newTime);
    }
  };

  const skipToSegment = (direction) => {
    let targetSegment;
    
    if (direction === 'prev') {
      targetSegment = Math.max(0, currentSegment - 1);
    } else {
      targetSegment = Math.min(segments.length - 1, currentSegment + 1);
    }
    
    if (segments[targetSegment] && audioRef.current) {
      audioRef.current.currentTime = segments[targetSegment].start;
    }
  };

  const handleVolumeChange = (e) => {
    const newVolume = parseFloat(e.target.value);
    setVolume(newVolume);
    if (audioRef.current) {
      audioRef.current.volume = newVolume;
    }
  };

  const handlePlaybackRateChange = (e) => {
    const newRate = parseFloat(e.target.value);
    setPlaybackRate(newRate);
    if (audioRef.current) {
      audioRef.current.playbackRate = newRate;
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-player">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={audioFile}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onPlay={() => setIsPlaying(true)}
        onPause={() => setIsPlaying(false)}
        onEnded={() => setIsPlaying(false)}
      />

      {/* Player Controls */}
      <div className="player-controls">
        <div className="main-controls">
          <button 
            onClick={() => skipToSegment('prev')}
            className="control-button"
            disabled={currentSegment === 0}
          >
            <SkipBack size={20} />
          </button>
          
          <button 
            onClick={togglePlayPause}
            className="play-pause-button"
          >
            {isPlaying ? <Pause size={24} /> : <Play size={24} />}
          </button>
          
          <button 
            onClick={() => skipToSegment('next')}
            className="control-button"
            disabled={currentSegment === segments.length - 1}
          >
            <SkipForward size={20} />
          </button>
        </div>

        <div className="time-display">
          <span className="current-time">{formatTime(currentTime)}</span>
          <span className="separator">/</span>
          <span className="total-time">{formatTime(duration)}</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="progress-container">
        <div 
          className="progress-bar" 
          onClick={handleSeek}
        >
          <div 
            className="progress-fill"
            style={{ width: `${(currentTime / duration) * 100}%` }}
          />
          
          {/* Segment markers */}
          {segments.map((segment, index) => (
            <div
              key={index}
              className={`segment-marker ${index === currentSegment ? 'current' : ''}`}
              style={{ left: `${(segment.start / duration) * 100}%` }}
              title={`Segment ${index + 1}: ${formatTime(segment.start)}`}
            />
          ))}
        </div>
      </div>

      {/* Additional Controls */}
      <div className="additional-controls">
        <div className="volume-control">
          <Volume2 size={16} />
          <input
            type="range"
            min="0"
            max="1"
            step="0.1"
            value={volume}
            onChange={handleVolumeChange}
            className="volume-slider"
          />
          <span className="volume-display">{Math.round(volume * 100)}%</span>
        </div>

        <div className="playback-rate-control">
          <label htmlFor="playback-rate">Speed:</label>
          <select
            id="playback-rate"
            value={playbackRate}
            onChange={handlePlaybackRateChange}
            className="playback-rate-select"
          >
            <option value="0.5">0.5x</option>
            <option value="0.75">0.75x</option>
            <option value="1.0">1x</option>
            <option value="1.25">1.25x</option>
            <option value="1.5">1.5x</option>
            <option value="2.0">2x</option>
          </select>
        </div>

        <div className="segment-info">
          Segment {currentSegment + 1} of {segments.length}
        </div>
      </div>

      <style jsx>{`
        .audio-player {
          background: #2A2B2F;
          border-radius: 8px;
          padding: 20px;
          margin-bottom: 24px;
        }

        .player-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .main-controls {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .control-button {
          background: none;
          border: 1px solid #666;
          color: #FFFFFF;
          padding: 8px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .control-button:hover:not(:disabled) {
          border-color: #4ECDC4;
          color: #4ECDC4;
        }

        .control-button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .play-pause-button {
          background: #4ECDC4;
          color: #1B1C20;
          border: none;
          padding: 12px;
          border-radius: 50%;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.2s ease;
        }

        .play-pause-button:hover {
          background: #45B7B8;
          transform: scale(1.05);
        }

        .time-display {
          font-family: 'Courier New', monospace;
          font-size: 16px;
          color: #FFFFFF;
        }

        .separator {
          margin: 0 8px;
          color: #888;
        }

        .progress-container {
          margin-bottom: 16px;
        }

        .progress-bar {
          position: relative;
          height: 8px;
          background: #444;
          border-radius: 4px;
          cursor: pointer;
          overflow: visible;
        }

        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #4ECDC4, #44A08D);
          border-radius: 4px;
          transition: width 0.1s ease;
        }

        .segment-marker {
          position: absolute;
          top: -2px;
          width: 2px;
          height: 12px;
          background: #f39c12;
          border-radius: 1px;
          opacity: 0.7;
          transition: all 0.2s ease;
        }

        .segment-marker.current {
          background: #4ECDC4;
          opacity: 1;
          height: 16px;
          top: -4px;
        }

        .additional-controls {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 16px;
          font-size: 14px;
        }

        .volume-control {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .volume-slider {
          width: 80px;
          accent-color: #4ECDC4;
        }

        .volume-display {
          min-width: 35px;
          text-align: right;
          color: #888;
        }

        .playback-rate-control {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .playback-rate-select {
          background: #1B1C20;
          color: #FFFFFF;
          border: 1px solid #666;
          padding: 4px 8px;
          border-radius: 4px;
        }

        .segment-info {
          color: #888;
          font-size: 12px;
        }

        @media (max-width: 768px) {
          .player-controls {
            flex-direction: column;
            gap: 12px;
          }

          .additional-controls {
            flex-direction: column;
            gap: 8px;
          }

          .volume-control,
          .playback-rate-control {
            justify-content: center;
          }
        }
      `}</style>
    </div>
  );
});

AudioPlayer.displayName = 'AudioPlayer';

export default AudioPlayer;