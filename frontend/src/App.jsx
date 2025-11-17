/**
 * Main App Component
 * Combines Timeline Sidebar, Upload Panel, and Chat Interface.
 */
import React, { useState, useEffect } from 'react';
import TimelineSidebar from './components/Timeline/TimelineSidebar';
import ChatInterface from './components/Chat/ChatInterface';
import UploadPanel from './components/Upload/UploadPanel';
import SourceSelector from './components/Sources/SourceSelector';
import SessionPanel from './components/Sessions/SessionPanel';
import {
  getDailyTimeline,
  listSources,
  getCurrentSession,
  removeSessionSource,
  deleteSource,
  downloadTimelineNotes,
  clearSession,
} from './services/api';
import './App.css';

function App() {
  const [timelines, setTimelines] = useState([]);
  const [highlightedDates, setHighlightedDates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState([]);
  const [selectedSourceId, setSelectedSourceId] = useState(null);
  const [session, setSession] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(true);
  const [selectedTimelineDate, setSelectedTimelineDate] = useState(null);

  // Load timeline data on mount
  useEffect(() => {
    loadTimeline();
    loadSources();
    loadSession();
  }, []);

  useEffect(() => {
    if (
      selectedSourceId &&
      !sources.some((source) => source.id === selectedSourceId)
    ) {
      setSelectedSourceId(null);
    }
  }, [sources, selectedSourceId]);

  useEffect(() => {
    if (!selectedTimelineDate && timelines.length > 0) {
      setSelectedTimelineDate(timelines[0].date);
    }
  }, [timelines, selectedTimelineDate]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      const response = await getDailyTimeline(1, 30);
      setTimelines(response.timelines);
    } catch (error) {
      console.error('Failed to load timeline:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDatesUsed = (dates) => {
    setHighlightedDates(dates);
  };

  const loadSources = async () => {
    try {
      const response = await listSources(1, 100);
      setSources(response.sources || []);
    } catch (error) {
      console.error('Failed to load sources:', error);
    }
  };

  const loadSession = async () => {
    try {
      setSessionLoading(true);
      const response = await getCurrentSession(1);
      setSession(response);
    } catch (error) {
      console.error('Failed to load session:', error);
    } finally {
      setSessionLoading(false);
    }
  };

  const handleUploadComplete = () => {
    // Reload timeline and sources after upload
    loadTimeline();
    loadSources();
    loadSession();
  };

  const handleSessionSourceRemove = async (sourceId) => {
    try {
      await removeSessionSource(sourceId, 1);
      if (selectedSourceId === sourceId) {
        setSelectedSourceId(null);
      }
      loadSession();
    } catch (error) {
      console.error('Failed to remove session source:', error);
    }
  };

  const handleClearSession = async () => {
    const confirmed = window.confirm('Clear all sources and interactions for today?');
    if (!confirmed) return;

    try {
      await clearSession(1);
      setSelectedSourceId(null);
      loadSession();
    } catch (error) {
      console.error('Failed to clear session:', error);
    }
  };

  const handleSourceDelete = async (sourceId) => {
    try {
      // eslint-disable-next-line no-alert
      const confirmed = window.confirm('Delete this source and all related events?');
      if (!confirmed) {
        return;
      }

      await deleteSource(sourceId, 1);

      if (selectedSourceId === sourceId) {
        setSelectedSourceId(null);
      }

      loadSources();
      loadSession();
      loadTimeline();
    } catch (error) {
      console.error('Failed to delete source:', error);
    }
  };

  const handleInteractionComplete = () => {
    loadSession();
    loadSources();
    loadTimeline();
  };

  const handleTimelineDateClick = (dateValue) => {
    setSelectedTimelineDate(dateValue);
  };

  const handleDownloadNotes = async (dateValue) => {
    try {
      const blob = await downloadTimelineNotes(1, dateValue);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `timeline_${dateValue}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download notes:', error);
      alert('Unable to download notes for this day.');
    }
  };

  return (
    <div className="app">
      <TimelineSidebar
        timelines={timelines}
        highlightedDates={highlightedDates}
        selectedDate={selectedTimelineDate}
        onDateClick={handleTimelineDateClick}
        onDownloadNotes={handleDownloadNotes}
      />
      <div className="main-content">
        <SessionPanel
          session={session}
          loading={sessionLoading}
          selectedSourceId={selectedSourceId}
          onSelectSource={setSelectedSourceId}
          onRemoveSource={handleSessionSourceRemove}
          onClearSession={handleClearSession}
        />
        <SourceSelector
          sources={sources}
          selectedSourceId={selectedSourceId}
          onSelect={setSelectedSourceId}
          onDelete={handleSourceDelete}
        />
        <UploadPanel onUploadComplete={handleUploadComplete} />
        <ChatInterface
          onDatesUsed={handleDatesUsed}
          selectedSourceId={selectedSourceId}
          selectedSource={
            sources.find((source) => source.id === selectedSourceId) || null
          }
          onInteractionComplete={handleInteractionComplete}
        />
      </div>
    </div>
  );
}

export default App;
