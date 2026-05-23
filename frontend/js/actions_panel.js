/* ═══════════════════════════════════════════════════════════
   CrowdPulse AI — Action Plan Panel
   ═══════════════════════════════════════════════════════════ */

class ActionsPanel {
  constructor() {
    this.container = document.getElementById('action-items-container');
    this.executeAllBtn = document.getElementById('execute-all-btn');
    this.priorityBadge = document.getElementById('action-priority');
    this.actions = [];

    // Action type to button style mapping
    this.actionStyles = {
      notify_fans:       { label: 'Notify Fans',       btnClass: 'action-btn-cyan',   icon: '📢' },
      notify:            { label: 'Notify',             btnClass: 'action-btn-cyan',   icon: '📢' },
      dispatch_staff:    { label: 'Dispatch Staff',     btnClass: 'action-btn-amber',  icon: '👮' },
      dispatch:          { label: 'Dispatch',           btnClass: 'action-btn-amber',  icon: '👮' },
      open_gate:         { label: 'Open Gate',          btnClass: 'action-btn-green',  icon: '🚪' },
      gate:              { label: 'Open Gate',          btnClass: 'action-btn-green',  icon: '🚪' },
      increase_staff:    { label: 'Increase Staff',     btnClass: 'action-btn-purple', icon: '👥' },
      staff:             { label: 'Staff Up',           btnClass: 'action-btn-purple', icon: '👥' },
      maintain_access:   { label: 'Maintain Access',    btnClass: 'action-btn-blue',   icon: '🔓' },
      maintain:          { label: 'Maintain',           btnClass: 'action-btn-blue',   icon: '🔓' },
      emergency:         { label: 'Emergency',          btnClass: 'action-btn-red',    icon: '🚨' },
      emergency_protocol:{ label: 'Emergency Protocol', btnClass: 'action-btn-red',    icon: '🚨' },
      alert:             { label: 'Alert',              btnClass: 'action-btn-amber',  icon: '⚠️' },
      monitor:           { label: 'Monitor',            btnClass: 'action-btn-blue',   icon: '👁️' },
      redirect:          { label: 'Redirect',           btnClass: 'action-btn-green',  icon: '↪️' },
      close_gate:        { label: 'Close Gate',         btnClass: 'action-btn-red',    icon: '🚫' }
    };

    this.defaultStyle = { label: 'Execute', btnClass: 'action-btn-cyan', icon: '⚡' };

    this._initExecuteAll();
  }

  /**
   * Render the action plan
   * @param {Object} actionPlan - { actions: [...], priority: 'high' }
   */
  updateActionPlan(actionPlan) {
    if (!actionPlan) return;

    // Handle different data formats
    let actionsArray = [];
    let priority = 'high';

    if (Array.isArray(actionPlan)) {
      actionsArray = actionPlan;
    } else if (actionPlan.actions && Array.isArray(actionPlan.actions)) {
      actionsArray = actionPlan.actions;
      priority = actionPlan.priority || 'high';
    } else if (actionPlan.recommended_actions) {
      actionsArray = actionPlan.recommended_actions;
      priority = actionPlan.priority || 'high';
    }

    this.actions = actionsArray;
    this._updatePriorityBadge(priority);
    this._renderActions();
  }

  _renderActions() {
    this.container.innerHTML = '';

    if (this.actions.length === 0) {
      this.container.innerHTML = `
        <div style="text-align: center; padding: 24px; color: var(--text-muted); width: 100%;">
          <div style="font-size: 2rem; margin-bottom: 8px;">✅</div>
          <div style="font-size: 0.85rem;">No actions required — all systems nominal</div>
        </div>
      `;
      return;
    }

    this.actions.forEach((action, index) => {
      const actionType = (action.type || action.action_type || 'execute').toLowerCase();
      const style = this.actionStyles[actionType] || this.defaultStyle;
      const description = action.description || action.text || action.message || '';

      const item = document.createElement('div');
      item.className = 'action-item';
      item.setAttribute('data-action-index', index);

      item.innerHTML = `
        <div class="action-number">${index + 1}</div>
        <div class="action-text">${this._escapeHtml(description)}</div>
        <button class="action-btn ${style.btnClass}" data-action-type="${actionType}" data-action-index="${index}">
          ${style.icon} ${style.label}
        </button>
      `;

      // Click handler for individual action button
      const btn = item.querySelector('.action-btn');
      btn.addEventListener('click', (e) => this._executeAction(e, actionType, index));

      this.container.appendChild(item);
    });
  }

  /**
   * Execute a single action
   */
  async _executeAction(event, actionType, index) {
    const btn = event.target.closest('.action-btn');
    if (btn.classList.contains('executed')) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '⏳ Executing...';
    btn.disabled = true;

    try {
      const response = await fetch(`/api/actions/${actionType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action_type: actionType,
          action_index: index,
          action: this.actions[index] || {}
        })
      });

      if (response.ok) {
        btn.innerHTML = '✅ Done';
        btn.classList.add('executed');
        this._showConfirmation(btn);
      } else {
        btn.innerHTML = '❌ Failed';
        setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
      }
    } catch (err) {
      console.error('[Actions] Execute error:', err);
      btn.innerHTML = '❌ Error';
      setTimeout(() => { btn.innerHTML = originalText; btn.disabled = false; }, 2000);
    }
  }

  /**
   * Initialize Execute All button
   */
  _initExecuteAll() {
    if (!this.executeAllBtn) return;

    this.executeAllBtn.addEventListener('click', async () => {
      if (this.executeAllBtn.classList.contains('executing')) return;

      const originalText = this.executeAllBtn.innerHTML;
      this.executeAllBtn.innerHTML = '⏳ Executing All Actions...';
      this.executeAllBtn.classList.add('executing');

      try {
        const response = await fetch('/api/actions/execute_all', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ actions: this.actions })
        });

        if (response.ok) {
          this.executeAllBtn.innerHTML = '✅ All Actions Executed Successfully';

          // Mark all action buttons as executed
          const allBtns = this.container.querySelectorAll('.action-btn');
          allBtns.forEach(btn => {
            btn.innerHTML = '✅ Done';
            btn.classList.add('executed');
            btn.disabled = true;
          });

          setTimeout(() => {
            this.executeAllBtn.innerHTML = originalText;
            this.executeAllBtn.classList.remove('executing');
          }, 3000);
        } else {
          this.executeAllBtn.innerHTML = '❌ Execution Failed';
          setTimeout(() => {
            this.executeAllBtn.innerHTML = originalText;
            this.executeAllBtn.classList.remove('executing');
          }, 2000);
        }
      } catch (err) {
        console.error('[Actions] Execute all error:', err);
        this.executeAllBtn.innerHTML = '❌ Connection Error';
        setTimeout(() => {
          this.executeAllBtn.innerHTML = originalText;
          this.executeAllBtn.classList.remove('executing');
        }, 2000);
      }
    });
  }

  /**
   * Update priority badge
   */
  _updatePriorityBadge(priority) {
    if (!this.priorityBadge) return;

    const p = (priority || 'high').toLowerCase();
    this.priorityBadge.className = 'priority-badge';

    switch (p) {
      case 'critical':
        this.priorityBadge.classList.add('priority-critical');
        this.priorityBadge.innerHTML = '<span class="priority-dot"></span> Critical Priority';
        break;
      case 'high':
        this.priorityBadge.classList.add('priority-high');
        this.priorityBadge.innerHTML = '<span class="priority-dot"></span> High Priority';
        break;
      default:
        this.priorityBadge.classList.add('priority-high');
        this.priorityBadge.innerHTML = '<span class="priority-dot"></span> ' + p.charAt(0).toUpperCase() + p.slice(1) + ' Priority';
    }
  }

  /**
   * Show a brief confirmation animation on a button
   */
  _showConfirmation(btn) {
    btn.style.transition = 'all 0.3s ease';
    btn.style.transform = 'scale(1.05)';
    setTimeout(() => {
      btn.style.transform = 'scale(1)';
    }, 200);
  }

  _escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Global instance
window.ActionsPanel = ActionsPanel;
