/**
 * API client for Timeline Thinker backend.
 */
import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  'https://timelinethinker-55205333609.europe-west1.run.app/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Query the Timeline Thinker with a question.
 */
export const query = async (question, userId = 1, sourceId = null) => {
  const payload = {
    user_id: userId,
    question: question,
  };

  if (sourceId) {
    payload.source_id = sourceId;
  }

  const response = await api.post('/query', payload);
  return response.data;
};

/**
 * Get daily timeline for a user.
 */
export const getDailyTimeline = async (userId = 1, days = 30) => {
  const response = await api.get('/timeline/daily', {
    params: { user_id: userId, days },
  });
  return response.data;
};

/**
 * Get topics for a user.
 */
export const getTopics = async (userId = 1, limit = 20) => {
  const response = await api.get('/timeline/topics', {
    params: { user_id: userId, limit },
  });
  return response.data;
};

/**
 * Ingest an audio file.
 */
export const ingestAudio = async (file, userId = 1, title = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);
  if (title) {
    formData.append('title', title);
  }

  const response = await api.post('/ingest/audio', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Ingest a document file.
 */
export const ingestDocument = async (file, userId = 1, title = null) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('user_id', userId);
  if (title) {
    formData.append('title', title);
  }

  const response = await api.post('/ingest/document', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

/**
 * Ingest a webpage by URL.
 */
export const ingestWebpage = async (url, userId = 1) => {
  const response = await api.post('/ingest/webpage', {
    url: url,
    user_id: userId,
  });
  return response.data;
};

/**
 * List previously ingested sources for a user.
 */
export const listSources = async (userId = 1, limit = 50) => {
  const response = await api.get('/sources', {
    params: { user_id: userId, limit },
  });
  return response.data;
};

/**
 * Permanently delete a source.
 */
export const deleteSource = async (sourceId, userId = 1) => {
  const response = await api.delete(`/sources/${sourceId}`, {
    params: { user_id: userId },
  });
  return response.data;
};

/**
 * Fetch the current day's session snapshot.
 */
export const getCurrentSession = async (userId = 1) => {
  const response = await api.get('/sessions/current', {
    params: { user_id: userId },
  });
  return response.data;
};

/**
 * Remove a source from today's session.
 */
export const removeSessionSource = async (sourceId, userId = 1) => {
  const response = await api.delete(`/sessions/current/source/${sourceId}`, {
    params: { user_id: userId },
  });
  return response.data;
};

export const downloadTimelineNotes = async (userId = 1, date) => {
  const response = await api.get('/timeline/day-notes', {
    params: { user_id: userId, target_date: date },
    responseType: 'blob',
  });
  return response.data;
};

export const clearSession = async (userId = 1) => {
  const response = await api.delete('/sessions/current', {
    params: { user_id: userId },
  });
  return response.data;
};

export default api;
