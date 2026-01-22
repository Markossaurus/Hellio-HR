import { login } from './api/auth.js';
import { isAuthenticated } from './auth/store.js';

// Redirect if already logged in
if (isAuthenticated()) {
  window.location.href = 'index.html';
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('login-form');
  const errorDiv = document.getElementById('login-error');
  const submitBtn = form.querySelector('button[type="submit"]');
  const originalBtnText = submitBtn.textContent;
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorDiv.textContent = '';
    errorDiv.style.display = 'none';
    
    // Disable button and show loading state
    submitBtn.disabled = true;
    submitBtn.textContent = 'Signing in...';
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
      await login(email, password);
      // Success - redirect handled in login function? No, the login function returns user.
      // We should redirect here.
      window.location.href = 'index.html';
    } catch (error) {
      errorDiv.textContent = error.message || 'Login failed. Please check your credentials.';
      errorDiv.style.display = 'block';
      
      // Reset button
      submitBtn.disabled = false;
      submitBtn.textContent = originalBtnText;
      
      // Shake animation for error
      const card = document.querySelector('.login-card');
      card.style.animation = 'none';
      card.offsetHeight; /* trigger reflow */
      card.style.animation = 'shake 0.4s ease-in-out';
    }
  });
});


