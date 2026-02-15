import { api } from './client.js';

export async function sendChatQuery(question, history = []) {
  try {
    const response = await api.post('/chat', { question, history, retrieval_mode: 'hybrid' });
    return {
      success: !response.error,
      answer: response.answer,
      sql: response.sql,
      rowCount: response.rowCount,
      columns: response.columns,
      error: response.error
    };
  } catch (error) {
    return {
      success: false,
      error: error.message || 'Failed to send chat query'
    };
  }
}
