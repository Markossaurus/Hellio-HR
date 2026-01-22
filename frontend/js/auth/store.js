const TOKEN_KEY = 'hellio_auth_token';
const USER_KEY = 'hellio_auth_user';

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
}

export function getUser() {
  const user = sessionStorage.getItem(USER_KEY);
  return user ? JSON.parse(user) : null;
}

export function setUser(user) {
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function isAuthenticated() {
  return !!getToken();
}
