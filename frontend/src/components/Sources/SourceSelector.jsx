/**
 * Source Selector Component
 * Lets the user pick which ingested source to focus queries on.
 */
import React from 'react';
import './SourceSelector.css';

const formatDate = (isoString) => {
  if (!isoString) return '';
  const date = new Date(isoString);
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  });
};

const SourceSelector = ({
  sources = [],
  selectedSourceId,
  onSelect,
  onDelete,
}) => {
  const handleSelectChange = (event) => {
    const value = event.target.value;
    onSelect(value ? Number(value) : null);
  };

  const handlePillClick = (sourceId) => {
    onSelect(sourceId === selectedSourceId ? null : sourceId);
  };

  const handleDelete = (event, sourceId) => {
    event.stopPropagation();
    if (onDelete) {
      onDelete(sourceId);
    }
  };

  return (
    <div className="source-selector">
      <div className="selector-header">
        <div>
          <h3>Focus Source</h3>
          <p className="selector-subtitle">
            Choose a document, page, or recording to chat about.
          </p>
        </div>
        {selectedSourceId && (
          <button className="clear-source" onClick={() => onSelect(null)}>
            Clear
          </button>
        )}
      </div>

      <select
        className="source-select"
        value={selectedSourceId || ''}
        onChange={handleSelectChange}
      >
        <option value="">All sources</option>
        {sources.map((source) => (
          <option key={source.id} value={source.id}>
            {source.title} ({source.source_type})
          </option>
        ))}
      </select>

      <div className="source-timeline">
        {sources.length === 0 ? (
          <div className="source-empty">
            <p>No sources yet. Upload files or add webpages to get started.</p>
          </div>
        ) : (
          sources.map((source) => {
            const isActive = selectedSourceId === source.id;
            return (
              <div
                key={source.id}
                className={`source-pill ${isActive ? 'active' : ''}`}
                onClick={() => handlePillClick(source.id)}
              >
                <div>
                  <div className="source-pill-title">{source.title}</div>
                  <div className="source-pill-meta">
                    {source.source_type} • {formatDate(source.created_at)}
                  </div>
                </div>
                <button
                  className="source-pill-remove"
                  onClick={(event) => handleDelete(event, source.id)}
                  title="Delete source"
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

export default SourceSelector;
