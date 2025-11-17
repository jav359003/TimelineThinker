/**
 * Upload Panel Component
 * Allows users to upload files and ingest content.
 */
import React, { useState } from 'react';
import './Upload.css';
import { ingestDocument, ingestAudio, ingestWebpage } from '../../services/api';

const UploadPanel = ({ onUploadComplete }) => {
  const [activeTab, setActiveTab] = useState('file');
  const [url, setUrl] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setMessage(`Uploading ${file.name}...`);

    try {
      const fileExtension = file.name.split('.').pop().toLowerCase();
      let result;

      if (['mp3', 'm4a', 'wav', 'ogg'].includes(fileExtension)) {
        // Audio file
        result = await ingestAudio(file, 1, file.name);
        setMessage(`✓ Audio "${result.title}" ingested! Created ${result.events_created} events.`);
      } else if (['pdf', 'md', 'txt'].includes(fileExtension)) {
        // Document file
        result = await ingestDocument(file, 1, file.name);
        setMessage(`✓ Document "${result.title}" ingested! Created ${result.events_created} events.`);
      } else {
        setMessage(`❌ Unsupported file type: ${fileExtension}`);
        setIsUploading(false);
        return;
      }

      if (onUploadComplete) {
        onUploadComplete();
      }

      // Clear the input
      event.target.value = '';
    } catch (error) {
      console.error('Upload failed:', error);
      setMessage(`❌ Upload failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const handleWebpageSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setIsUploading(true);
    setMessage(`Ingesting webpage from ${url}...`);

    try {
      const result = await ingestWebpage(url, 1);
      setMessage(`✓ Webpage "${result.title}" ingested! Created ${result.events_created} events.`);
      setUrl('');

      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error('Webpage ingestion failed:', error);
      setMessage(`❌ Ingestion failed: ${error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="upload-panel">
      <div className="upload-header">
        <h3>Add Content</h3>
      </div>

      <div className="upload-tabs">
        <button
          className={`tab ${activeTab === 'file' ? 'active' : ''}`}
          onClick={() => setActiveTab('file')}
        >
          📄 Files
        </button>
        <button
          className={`tab ${activeTab === 'web' ? 'active' : ''}`}
          onClick={() => setActiveTab('web')}
        >
          🌐 Web
        </button>
      </div>

      <div className="upload-content">
        {activeTab === 'file' && (
          <div className="file-upload">
            <label htmlFor="file-input" className="file-upload-label">
              <div className="file-upload-icon">📁</div>
              <div className="file-upload-text">
                Click to upload or drag and drop
              </div>
              <div className="file-upload-hint">
                Audio: MP3, M4A, WAV • Documents: PDF, MD, TXT
              </div>
            </label>
            <input
              id="file-input"
              type="file"
              accept=".pdf,.md,.txt,.mp3,.m4a,.wav,.ogg"
              onChange={handleFileUpload}
              disabled={isUploading}
              className="file-input"
            />
          </div>
        )}

        {activeTab === 'web' && (
          <div className="web-upload">
            <form onSubmit={handleWebpageSubmit}>
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="Enter webpage URL (e.g., https://example.com/article)"
                disabled={isUploading}
                className="url-input"
              />
              <button
                type="submit"
                disabled={isUploading || !url.trim()}
                className="url-submit"
              >
                {isUploading ? 'Ingesting...' : 'Add Page'}
              </button>
            </form>
            <p className="web-hint">
              We'll extract and save the main content from the page
            </p>
          </div>
        )}
      </div>

      {message && (
        <div className={`upload-message ${message.startsWith('✓') ? 'success' : message.startsWith('❌') ? 'error' : 'info'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

export default UploadPanel;
