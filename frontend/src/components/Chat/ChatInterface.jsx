/**
 * Chat Interface Component
 * Main chat container with messages and input.
 */
import React, { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import InputBox from './InputBox';
import './Chat.css';
import { query as queryAPI } from '../../services/api';

const ChatInterface = ({
  onDatesUsed,
  selectedSourceId = null,
  selectedSource = null,
  onInteractionComplete,
}) => {
  const initialMessage = {
    role: 'assistant',
    content:
      "Hello! I'm your Timeline Thinker. Ask me anything about the information you've shared with me.",
    timestamp: new Date(),
  };
  const [messages, setMessages] = useState([initialMessage]);
  const [isLoading, setIsLoading] = useState(false);
  const lastSourceIdRef = useRef(selectedSourceId);

  const handleSendMessage = async (userMessage) => {
    // Add user message to chat
    const userMsg = {
      role: 'user',
      content: userMessage,
      timestamp: new Date(),
      context: selectedSource ? `Source: ${selectedSource.title}` : undefined,
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);

    try {
      // Call API
      const response = await queryAPI(userMessage, 1, selectedSourceId);

      // Add assistant response to chat
      const assistantMsg = {
        role: 'assistant',
        content: response.answer,
        timestamp: new Date(),
        metadata: selectedSource
          ? {
              sourceTitle: selectedSource.title,
              sourceType: selectedSource.source_type,
              sourceId: selectedSource.id,
            }
          : undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);

      if (onDatesUsed && response.dates_used) {
        onDatesUsed(response.dates_used);
      }

      if (onInteractionComplete) {
        onInteractionComplete();
      }
    } catch (error) {
      console.error('Query failed:', error);
      const errorMsg = {
        role: 'assistant',
        content: 'Sorry, I encountered an error while processing your question. Please try again.',
        timestamp: new Date(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (lastSourceIdRef.current === selectedSourceId) {
      return;
    }

    lastSourceIdRef.current = selectedSourceId;

    const focusMessage = selectedSource
      ? `Switched focus to "${selectedSource.title}". Ask a question about this source to pull its context.`
      : 'Cleared focused source. Ask about anything in your knowledge base.';

    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: focusMessage,
        timestamp: new Date(),
      },
    ]);
  }, [selectedSourceId, selectedSource]);

  return (
    <div className="chat-interface">
      <div className="chat-header">
        <h1>Timeline Thinker</h1>
        <p>
          {selectedSource
            ? `Focused on: ${selectedSource.title}`
            : 'Ask questions about your knowledge base'}
        </p>
      </div>

      <MessageList messages={messages} isLoading={isLoading} />

      <InputBox onSend={handleSendMessage} disabled={isLoading} />
    </div>
  );
};

export default ChatInterface;
