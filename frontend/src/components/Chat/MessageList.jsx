/**
 * Message List Component
 * Displays all chat messages with auto-scroll.
 */
import React, { useEffect, useRef } from 'react';

const MessageList = ({ messages, isLoading }) => {
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="message-list">
      {messages.map((message, index) => (
        <div
          key={index}
          className={`message ${message.role} ${message.isError ? 'error' : ''}`}
        >
          <div className="message-header">
            <span className="message-role">
              {message.role === 'user' ? 'You' : 'Timeline Thinker'}
            </span>
            <span className="message-time">{formatTime(message.timestamp)}</span>
          </div>
          <div className="message-content">
            {message.context && <div className="message-context">{message.context}</div>}
            {message.content}
          </div>

          {message.metadata && (
            <div className="message-metadata">
              {message.metadata.sourceTitle && (
                <small>Source: {message.metadata.sourceTitle}</small>
              )}
              {message.metadata.datesUsed && (
                <small>
                  {`Dates referenced: ${message.metadata.datesUsed
                    .map((d) => new Date(d).toLocaleDateString())
                    .join(', ')}`}
                </small>
              )}
            </div>
          )}
        </div>
      ))}

      {isLoading && (
        <div className="message assistant loading">
          <div className="message-header">
            <span className="message-role">Timeline Thinker</span>
          </div>
          <div className="message-content">
            <div className="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
