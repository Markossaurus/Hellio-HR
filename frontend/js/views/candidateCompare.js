import { getCandidateById } from '../data/candidates.js';

export function renderCandidateCompare(container, candidateId1, candidateId2) {
  const c1 = candidateId1 ? getCandidateById(candidateId1) : null;
  const c2 = candidateId2 ? getCandidateById(candidateId2) : null;
  
  container.innerHTML = `
    <div class="compare-container">
      <div class="compare-panel card">
        ${c1 ? renderComparePanel(c1) : '<div class="compare-placeholder">Select first candidate</div>'}
      </div>
      <div class="compare-panel card">
        ${c2 ? renderComparePanel(c2) : '<div class="compare-placeholder">Select second candidate</div>'}
      </div>
    </div>
  `;
  
  if (c1 && c2) {
    highlightDifferences(container, c1, c2);
  }
}

function renderComparePanel(candidate) {
  return `
    <div class="card-header">
      <h3 class="card-title">${candidate.name}</h3>
    </div>
    <div class="candidate-title mb-2">${candidate.title}</div>
    
    <div class="profile-section">
      <h3>Skills</h3>
      <div class="skills" data-compare="skills">
        ${candidate.skills.map(s => `<span class="skill-tag" data-skill="${s.name.toLowerCase()}">${s.name}</span>`).join('')}
      </div>
    </div>
    
    <div class="profile-section">
      <h3>Experience</h3>
      <div data-compare="experience">
        <div class="text-sm mb-2"><strong>Total:</strong> ${calculateTotalExperience(candidate.experience)} years</div>
        <div class="scrollable-list">
        ${candidate.experience.map(exp => `
          <div class="timeline-item">
            <div class="timeline-title">${exp.title}</div>
            <div class="timeline-subtitle">${exp.company}</div>
          </div>
        `).join('')}
        </div>
      </div>
    </div>
    
    <div class="profile-section">
      <h3>Education</h3>
      <div data-compare="education">
        ${candidate.education.map(edu => `
          <div class="timeline-item">
            <div class="timeline-title">${edu.degree}</div>
            <div class="timeline-subtitle">${edu.institution}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function calculateTotalExperience(experience) {
  if (!experience.length) return 0;
  
  const ranges = experience
    .map(exp => {
      const start = parseDate(exp.startDate);
      const end = exp.endDate === 'present' ? new Date() : parseDate(exp.endDate);
      return start && end ? { start: start.getTime(), end: end.getTime() } : null;
    })
    .filter(Boolean)
    .sort((a, b) => a.start - b.start);
  
  if (!ranges.length) return 0;
  
  const merged = [ranges[0]];
  for (let i = 1; i < ranges.length; i++) {
    const last = merged[merged.length - 1];
    if (ranges[i].start <= last.end) {
      last.end = Math.max(last.end, ranges[i].end);
    } else {
      merged.push(ranges[i]);
    }
  }
  
  const totalMonths = merged.reduce((sum, r) => {
    const startDate = new Date(r.start);
    const endDate = new Date(r.end);
    return sum + (endDate.getFullYear() - startDate.getFullYear()) * 12 + (endDate.getMonth() - startDate.getMonth());
  }, 0);
  
  return Math.round(totalMonths / 12 * 10) / 10;
}

function parseDate(dateStr) {
  if (!dateStr) return null;
  const [year, month] = dateStr.split('-').map(Number);
  return new Date(year, (month || 1) - 1);
}

function highlightDifferences(container, c1, c2) {
  const panels = container.querySelectorAll('.compare-panel');
  const skills1 = new Set(c1.skills.map(s => s.name.toLowerCase()));
  const skills2 = new Set(c2.skills.map(s => s.name.toLowerCase()));
  
  panels.forEach((panel, idx) => {
    const currentSkills = idx === 0 ? skills1 : skills2;
    const otherSkills = idx === 0 ? skills2 : skills1;
    
    panel.querySelectorAll('[data-skill]').forEach(tag => {
      const skillName = tag.dataset.skill;
      if (otherSkills.has(skillName)) {
        tag.classList.add('diff-match');
      } else {
        tag.classList.add('diff-highlight');
      }
    });
  });
}
