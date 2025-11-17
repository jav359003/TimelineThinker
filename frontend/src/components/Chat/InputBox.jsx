/**
 * Input Box Component
 * Text input for user questions.
 */
import React, { useState } from 'react';

const InputBox = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="input-box">
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Ask a question about your knowledge..."
          disabled={disabled}
          className="message-input"
        />
        <button type="submit" disabled={disabled || !input.trim()} className="send-button">
          Send
        </button>
      </form>
    </div>
  );
};

export default InputBox;
