import { request } from './client.js';
import { setToken, setUser, clearToken } from '../auth/store.js';

export async function login(email, password) {
  const response = await request('/auth/login', {
    method: 'POST',
    body: { email, password },
    auth: false,  // Don't send token for login
  });
  
  const token = response.access_token || response.token;
  
  if (!token) {
    throw new Error('No access token received');
  }

  setToken(token);
  

  if (response.user) {
    setUser(response.user);
  } else {
    try {
        const user = await request('/users/me');
        setUser(user);
        return user;
    } catch (e) {
        console.warn('Could not fetch user details', e);
    }
  }
  
  return response.user;
}

export function logout() {
  clearToken();
  window.location.href = 'login.html';
}
