import { getCandidateById } from '../data/candidates.js';
import { getPositionById } from '../data/positions.js';

export function renderCandidateProfile(container, candidateId, { onAddPosition, onRemovePosition }) {
  const candidate = getCandidateById(candidateId);
  
  if (!candidate) {
    container.innerHTML = `<div class="empty-state">Select a candidate to view their profile</div>`;
    return;
  }
  
  const positions = candidate.positionIds.map(id => getPositionById(id)).filter(Boolean);
  
  container.innerHTML = `
    <div class="card">
      <div class="card-header">
        <div>
          <h2 class="card-title">${candidate.name}</h2>
          <div class="candidate-title">${candidate.title}</div>
        </div>
        ${candidate.cvDocument ? `
          <a href="${candidate.cvDocument.path}" target="_blank" class="cv-link">
            📄 View CV
          </a>
        ` : ''}
      </div>
      
      <div class="profile-section">
        <h3>Contact</h3>
        <div class="text-sm">${candidate.email || '—'}</div>
        <div class="text-sm">${candidate.phone || '—'}</div>
        <div class="text-sm">${candidate.location || '—'}</div>
      </div>
      
      ${candidate.summary ? `
        <div class="profile-section">
          <h3>Summary</h3>
          <p class="text-sm">${candidate.summary}</p>
        </div>
      ` : ''}
      
      <div class="profile-section">
        <h3>Skills</h3>
        <div class="skills">
          ${candidate.skills.length > 0 
            ? candidate.skills.map(s => `<span class="skill-tag">${s.name}</span>`).join('')
            : '<span class="text-muted text-sm">No skills listed</span>'
          }
        </div>
      </div>
      
      <div class="profile-section">
        <h3>Experience</h3>
        ${candidate.experience.length > 0 
          ? candidate.experience.map(exp => `
            <div class="timeline-item">
              <div class="timeline-title">${exp.title}</div>
              <div class="timeline-subtitle">${exp.company}</div>
              <div class="timeline-date">${formatDateRange(exp.startDate, exp.endDate)}</div>
            </div>
          `).join('')
          : '<span class="text-muted text-sm">No experience listed</span>'
        }
      </div>
      
      <div class="profile-section">
        <h3>Education</h3>
        ${candidate.education.length > 0 
          ? candidate.education.map(edu => `
            <div class="timeline-item">
              <div class="timeline-title">${edu.degree} in ${edu.field}</div>
              <div class="timeline-subtitle">${edu.institution}</div>
              <div class="timeline-date">${formatDateRange(edu.startDate, edu.endDate)}</div>
            </div>
          `).join('')
          : '<span class="text-muted text-sm">No education listed</span>'
        }
      </div>
      
      <div class="profile-section">
        <h3>Applied Positions</h3>
        <div id="position-list">
          ${positions.length > 0 
            ? positions.map(p => `
              <div class="flex" style="justify-content: space-between; align-items: center; padding: 0.5rem 0;">
                <span class="text-sm">${p.title}</span>
                <button class="btn btn-sm btn-outline btn-remove-position" data-position-id="${p.id}">Remove</button>
              </div>
            `).join('')
            : '<span class="text-muted text-sm">No positions assigned</span>'
          }
        </div>
        <button class="btn btn-sm btn-outline mt-1" id="btn-add-position">+ Add Position</button>
      </div>
    </div>
  `;
  
  container.querySelector('#btn-add-position')?.addEventListener('click', () => {
    onAddPosition?.(candidateId);
  });
  
  container.querySelectorAll('.btn-remove-position').forEach(btn => {
    btn.addEventListener('click', () => {
      onRemovePosition?.(candidateId, btn.dataset.positionId);
    });
  });
}

function formatDateRange(start, end) {
  const startStr = start || '?';
  const endStr = end === 'present' ? 'Present' : (end || '?');
  return `${startStr} – ${endStr}`;
}
