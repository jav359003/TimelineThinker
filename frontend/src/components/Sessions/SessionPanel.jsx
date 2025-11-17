/**
 * Session Panel
 * Shows today's session summary and active sources with remove buttons.
 */
import React from 'react';
import './SessionPanel.css';

const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleTimeString('en-US', { hour: 'numeric', minute: 'numeric' });
};

const SessionPanel = ({
  session,
  loading,
  selectedSourceId,
  onSelectSource,
  onRemoveSource,
  onClearSession,
}) => {
  const sources = session?.sources || [];
  const summary = session?.summary;
  const sessionDate = session?.date;

  return (
    <div className="session-panel">
      <div className="session-header">
        <div>
          <h3>Today's Session</h3>
          <p className="session-date">
            {sessionDate || 'No session started yet'}
          </p>
        </div>
        {onClearSession && (
          <button
            className="session-clear-button"
            onClick={onClearSession}
          >
            Clear All
          </button>
        )}
      </div>

      <div className="session-summary">
        {loading ? (
          <p className="session-summary-text">Summarizing...</p>
        ) : summary ? (
          <p className="session-summary-text">{summary}</p>
        ) : (
          <p className="session-summary-placeholder">
            Ask a question to start building today's session summary.
          </p>
        )}
      </div>

      <div className="session-sources-header">
        <h4>Session Sources</h4>
        <p className="session-sources-hint">
          Sources you’ve chatted about today
        </p>
      </div>

      <div className="session-sources">
        {sources.length === 0 ? (
          <div className="session-empty">
            <p>No sources in this session yet.</p>
            <p className="session-empty-hint">
              Select a source and ask a question to add it.
            </p>
          </div>
        ) : (
          sources.map((source) => {
            const isSelected = selectedSourceId === source.source_id;
            return (
              <div
                key={source.source_id}
                className={`session-source-card ${
                  isSelected ? 'selected' : ''
                }`}
                onClick={() =>
                  onSelectSource(
                    isSelected ? null : source.source_id
                  )
                }
              >
                <div className="session-source-content">
                  <div className="session-source-title">{source.title}</div>
                  <div className="session-source-meta">
                    {source.source_type} • Added {formatDate(source.added_at)}
                  </div>
                </div>
                <button
                  className="session-source-remove"
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemoveSource(source.source_id);
                  }}
                >
                  ×
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default SessionPanel;
