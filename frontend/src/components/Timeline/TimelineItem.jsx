/**
 * Timeline Item Component
 * Displays a single day's timeline entry.
 */
import React from 'react';

const TimelineItem = ({
  date,
  summary,
  eventCount,
  isHighlighted,
  onClick,
  onDownload,
}) => {
  // Format date
  const dateObj = new Date(date + 'T00:00:00');
  const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' });
  const monthDay = dateObj.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

  return (
    <div
      className={`timeline-item ${isHighlighted ? 'highlighted' : ''}`}
      onClick={() => onClick && onClick(date)}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div className="timeline-date">
        <div className="timeline-day">{dayName}</div>
        <div className="timeline-month-day">{monthDay}</div>
      </div>

      <div className="timeline-content">
        {summary ? (
          <p className="timeline-summary">{summary}</p>
        ) : (
          <p className="timeline-no-summary">No summary available</p>
        )}
        <div className="timeline-actions">
          <span className="timeline-event-count">{eventCount} events</span>
          <button
            className="timeline-notes-button"
            onClick={(e) => {
              e.stopPropagation();
              onDownload && onDownload();
            }}
          >
            Get Notes
          </button>
        </div>
      </div>
    </div>
  );
};

export default TimelineItem;
