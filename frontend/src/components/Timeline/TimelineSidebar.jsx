/**
 * Timeline Sidebar Component
 * Displays daily timeline entries in a scrollable sidebar.
 */
import React from 'react';
import TimelineItem from './TimelineItem';
import './Timeline.css';

const TimelineSidebar = ({
  timelines,
  highlightedDates = [],
  selectedDate,
  onDateClick,
  onDownloadNotes,
}) => {
  const handleDateClick = (date) => {
    if (onDateClick) {
      onDateClick(date);
    }
  };

  return (
    <div className="timeline-sidebar">
      <div className="timeline-header">
        <h2>Timeline</h2>
        <p className="timeline-subtitle">{timelines.length} days</p>
      </div>

      <div className="timeline-list">
        {timelines.length === 0 ? (
          <div className="timeline-empty">
            <p>No timeline entries yet.</p>
            <p className="timeline-empty-hint">
              Upload documents or add content to start building your Timeline Thinker.
            </p>
          </div>
        ) : (
          timelines.map((timeline) => (
            <TimelineItem
              key={timeline.date}
              date={timeline.date}
              summary={timeline.summary}
              eventCount={timeline.event_count}
              isHighlighted={
                highlightedDates.includes(timeline.date) || selectedDate === timeline.date
              }
              onClick={handleDateClick}
              onDownload={() => onDownloadNotes && onDownloadNotes(timeline.date)}
            />
          ))
        )}
      </div>

    </div>
  );
};

export default TimelineSidebar;
