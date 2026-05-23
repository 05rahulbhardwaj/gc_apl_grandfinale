/* ═══════════════════════════════════════════════════════════
   CrowdPulse AI — Agent Reasoning Panel
   ═══════════════════════════════════════════════════════════ */

class AgentsPanel {
  constructor() {
    this.container = document.getElementById('agent-messages-container');
    this.maxMessages = 50;
    this.messageCount = 0;

    // Agent type definitions
    this.agentConfig = {
      crowd: {
        icon: '👁️',
        name: 'Crowd Monitor',
        cssClass: 'crowd-agent',
        nameClass: 'crowd'
      },
      crowd_monitor: {
        icon: '👁️',
        name: 'Crowd Monitor',
        cssClass: 'crowd-agent',
        nameClass: 'crowd'
      },
      ticketing: {
        icon: '🎫',
        name: 'Ticketing Agent',
        cssClass: 'ticketing-agent',
        nameClass: 'ticketing'
      },
      ticket: {
        icon: '🎫',
        name: 'Ticketing Agent',
        cssClass: 'ticketing-agent',
        nameClass: 'ticketing'
      },
      route: {
        icon: '🗺️',
        name: 'Route Planner',
        cssClass: 'route-agent',
        nameClass: 'route'
      },
      route_planner: {
        icon: '🗺️',
        name: 'Route Planner',
        cssClass: 'route-agent',
        nameClass: 'route'
      },
      weather: {
        icon: '🌤️',
        name: 'Weather Agent',
        cssClass: 'weather-agent',
        nameClass: 'weather'
      },
      emergency: {
        icon: '🚨',
        name: 'Emergency Response',
        cssClass: 'emergency-agent',
        nameClass: 'emergency'
      },
      fan: {
        icon: '📣',
        name: 'Fan Experience',
        cssClass: 'fan-agent',
        nameClass: 'fan'
      },
      fan_experience: {
        icon: '📣',
        name: 'Fan Experience',
        cssClass: 'fan-agent',
        nameClass: 'fan'
      },
      coordinator: {
        icon: '🧠',
        name: 'Coordinator',
        cssClass: 'coordinator-agent',
        nameClass: 'coordinator'
      },
      safety: {
        icon: '🛡️',
        name: 'Safety Agent',
        cssClass: 'emergency-agent',
        nameClass: 'emergency'
      }
    };

    // Default agent config for unknown types
    this.defaultAgent = {
      icon: '🤖',
      name: 'AI Agent',
      cssClass: 'crowd-agent',
      nameClass: 'crowd'
    };
  }

  /**
   * Add a new agent message to the panel
   * @param {Object} agentResponse - { agent_type, summary, details, timestamp, agent_name }
   */
  addAgentMessage(agentResponse) {
    if (!agentResponse) return;

    const agentType = (agentResponse.agent_type || agentResponse.type || 'unknown').toLowerCase();
    const config = this.agentConfig[agentType] || this.defaultAgent;

    const agentName = agentResponse.agent_name || config.name;
    const summary = agentResponse.summary || agentResponse.message || agentResponse.content || '';
    const details = agentResponse.details || agentResponse.reasoning || '';
    const timestamp = agentResponse.timestamp
      ? new Date(agentResponse.timestamp).toLocaleTimeString()
      : new Date().toLocaleTimeString();

    const msgEl = document.createElement('div');
    msgEl.className = `agent-message ${config.cssClass}`;

    let detailsHtml = '';
    if (details) {
      const detailId = `detail-${Date.now()}-${this.messageCount}`;
      detailsHtml = `
        <div class="agent-msg-details truncated" id="${detailId}">${this._escapeHtml(details)}</div>
        <button class="agent-expand-btn" data-target="${detailId}">Show more ▾</button>
      `;
    }

    msgEl.innerHTML = `
      <div class="agent-msg-header">
        <div class="agent-identity">
          <span class="agent-icon">${config.icon}</span>
          <span class="agent-name ${config.nameClass}">${this._escapeHtml(agentName)}</span>
        </div>
        <span class="agent-timestamp">${timestamp}</span>
      </div>
      ${summary ? `<div class="agent-msg-summary">${this._escapeHtml(summary)}</div>` : ''}
      ${detailsHtml}
    `;

    // Add expand/collapse handler
    const expandBtn = msgEl.querySelector('.agent-expand-btn');
    if (expandBtn) {
      expandBtn.addEventListener('click', () => {
        const targetEl = msgEl.querySelector(`#${expandBtn.dataset.target}`);
        if (targetEl) {
          const isTruncated = targetEl.classList.contains('truncated');
          targetEl.classList.toggle('truncated');
          expandBtn.textContent = isTruncated ? 'Show less ▴' : 'Show more ▾';
        }
      });
    }

    // Append message
    this.container.appendChild(msgEl);
    this.messageCount++;

    // Enforce max messages
    while (this.container.children.length > this.maxMessages) {
      this.container.removeChild(this.container.firstChild);
    }

    // Auto-scroll to bottom
    this._scrollToBottom();
  }

  /**
   * Add multiple agent messages from state
   */
  setAgentMessages(messages) {
    if (!Array.isArray(messages)) return;
    this.clearMessages();
    messages.forEach(msg => this.addAgentMessage(msg));
  }

  /**
   * Clear all messages
   */
  clearMessages() {
    this.container.innerHTML = '';
    this.messageCount = 0;
  }

  /**
   * Scroll to bottom of messages container
   */
  _scrollToBottom() {
    requestAnimationFrame(() => {
      this.container.scrollTop = this.container.scrollHeight;
    });
  }

  _escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Global instance
window.AgentsPanel = AgentsPanel;
