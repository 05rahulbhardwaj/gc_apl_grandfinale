/* ═══════════════════════════════════════════════════════════
   CrowdPulse AI — WebSocket Manager (Socket.IO)
   ═══════════════════════════════════════════════════════════ */

class WebSocketManager {
  constructor() {
    this.socket = null;
    this.listeners = {};
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 20;
  }

  /**
   * Connect to the Socket.IO server
   */
  connect() {
    try {
      this.socket = io({
        path: '/ws/socket.io',
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000,
        reconnectionAttempts: this.maxReconnectAttempts,
        timeout: 10000
      });

      // ─── Connection Events ───
      this.socket.on('connect', () => {
        this.connected = true;
        this.reconnectAttempts = 0;
        console.log('[WS] Connected:', this.socket.id);
        this._updateStatus('connected');
        this._dispatch('connection_status', { connected: true });
      });

      this.socket.on('disconnect', (reason) => {
        this.connected = false;
        console.warn('[WS] Disconnected:', reason);
        this._updateStatus('disconnected');
        this._dispatch('connection_status', { connected: false, reason });
      });

      this.socket.on('connect_error', (error) => {
        this.reconnectAttempts++;
        console.error('[WS] Connection error:', error.message);
        this._updateStatus('error');
        this._dispatch('connection_status', { connected: false, error: error.message });
      });

      this.socket.on('reconnect', (attemptNumber) => {
        console.log('[WS] Reconnected after', attemptNumber, 'attempts');
        this._updateStatus('connected');
      });

      this.socket.on('reconnect_attempt', (attemptNumber) => {
        console.log('[WS] Reconnection attempt:', attemptNumber);
        this._updateStatus('reconnecting');
      });

      // ─── Application Events ───
      this.socket.on('state_update', (data) => {
        console.log('[WS] State update received');
        this._dispatch('state_update', data);
      });

      this.socket.on('agent_message', (data) => {
        console.log('[WS] Agent message:', data.agent_type || 'unknown');
        this._dispatch('agent_message', data);
      });

      this.socket.on('alert', (data) => {
        console.log('[WS] Alert:', data.severity || 'info');
        this._dispatch('alert', data);
      });

      this.socket.on('action_executed', (data) => {
        console.log('[WS] Action executed:', data.action_type || 'unknown');
        this._dispatch('action_executed', data);
      });

      this.socket.on('ticker_update', (data) => {
        this._dispatch('ticker_update', data);
      });

      this.socket.on('scenario_update', (data) => {
        console.log('[WS] Scenario update:', data.status || '');
        this._dispatch('scenario_update', data);
      });

    } catch (err) {
      console.error('[WS] Failed to initialize Socket.IO:', err);
      this._updateStatus('error');
    }
  }

  /**
   * Register an event listener
   */
  on(event, callback) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(callback);
  }

  /**
   * Remove an event listener
   */
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
  }

  /**
   * Emit an event to the server
   */
  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('[WS] Cannot emit, not connected');
    }
  }

  /**
   * Dispatch event to registered listeners
   */
  _dispatch(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (err) {
          console.error(`[WS] Error in listener for "${event}":`, err);
        }
      });
    }
  }

  /**
   * Update the system status indicator in the UI
   */
  _updateStatus(status) {
    const statusEl = document.getElementById('system-status');
    if (!statusEl) return;

    const dot = statusEl.querySelector('.status-dot');
    const text = statusEl.querySelector('.status-text');

    // Remove existing status classes
    dot.classList.remove('status-green', 'status-amber', 'status-red');

    switch (status) {
      case 'connected':
        dot.classList.add('status-green');
        text.textContent = 'All Systems Operational';
        text.style.color = 'var(--accent-green)';
        statusEl.style.background = 'var(--accent-green-dim)';
        statusEl.style.borderColor = 'rgba(34, 197, 94, 0.2)';
        break;
      case 'disconnected':
        dot.classList.add('status-amber');
        text.textContent = 'Disconnected';
        text.style.color = 'var(--accent-amber)';
        statusEl.style.background = 'var(--accent-amber-dim)';
        statusEl.style.borderColor = 'rgba(245, 158, 11, 0.2)';
        break;
      case 'reconnecting':
        dot.classList.add('status-amber');
        text.textContent = 'Reconnecting...';
        text.style.color = 'var(--accent-amber)';
        statusEl.style.background = 'var(--accent-amber-dim)';
        statusEl.style.borderColor = 'rgba(245, 158, 11, 0.2)';
        break;
      case 'error':
        dot.classList.add('status-red');
        text.textContent = 'Connection Error';
        text.style.color = 'var(--accent-red)';
        statusEl.style.background = 'var(--accent-red-dim)';
        statusEl.style.borderColor = 'rgba(239, 68, 68, 0.2)';
        break;
    }
  }

  /**
   * Disconnect from the server
   */
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  /**
   * Check if currently connected
   */
  isConnected() {
    return this.connected;
  }
}

// Global singleton
window.wsManager = new WebSocketManager();
