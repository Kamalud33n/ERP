/**
 * Content Enhancer - Dynamic, responsive UI improvements
 * - Context-aware emojis
 * - Rich content cards
 * - Dynamic greetings
 * - Status badges with animations
 */

const ContentEnhancer = {
  // Responsive emoji system based on context
  emoji: {
    getTimeGreeting: () => {
      const hour = new Date().getHours();
      if (hour < 12) return { emoji: '🌅', text: 'Good Morning' };
      if (hour < 17) return { emoji: '☀️', text: 'Good Afternoon' };
      return { emoji: '🌙', text: 'Good Evening' };
    },

    getStatusEmoji: (status) => {
      const map = {
        'pending': { emoji: '⏳', color: '#f59e0b', bg: '#fef3c7' },
        'approved': { emoji: '✅', color: '#10b981', bg: '#d1fae5' },
        'rejected': { emoji: '❌', color: '#ef4444', bg: '#fee2e2' },
        'completed': { emoji: '🎉', color: '#8b5cf6', bg: '#ede9fe' },
        'in_progress': { emoji: '⚙️', color: '#3b82f6', bg: '#dbeafe' },
        'on_leave': { emoji: '🏖️', color: '#ec4899', bg: '#fce7f3' },
        'present': { emoji: '✔️', color: '#10b981', bg: '#d1fae5' },
        'absent': { emoji: '❌', color: '#ef4444', bg: '#fee2e2' },
        'late': { emoji: '⏰', color: '#f59e0b', bg: '#fef3c7' },
      };
      return map[status] || { emoji: '📌', color: '#6b7280', bg: '#f3f4f6' };
    },

    getDataEmoji: (value, type = 'number') => {
      if (type === 'count') {
        if (value === 0) return '🔳';
        if (value < 5) return '🟢';
        if (value < 20) return '🟡';
        return '🔴';
      }
      if (type === 'money') {
        if (value === 0) return '💤';
        if (value < 10000) return '💵';
        if (value < 50000) return '💴';
        return '💰';
      }
      return '📊';
    },

    getPriorityEmoji: (priority) => {
      const map = {
        'high': { emoji: '🔴', color: '#ef4444' },
        'medium': { emoji: '🟡', color: '#f59e0b' },
        'low': { emoji: '🟢', color: '#10b981' },
      };
      return map[priority] || { emoji: '⚪', color: '#6b7280' };
    },

    getDepartmentEmoji: (dept) => {
      const map = {
        'HR': '👥',
        'IT': '💻',
        'Finance': '💰',
        'Sales': '📈',
        'Marketing': '📢',
        'Operations': '⚙️',
        'Healthcare': '🏥',
        'Admin': '👨‍💼',
        'Medical': '🩺',
        'Nursing': '👩‍⚕️',
        'Pharmacy': '💊',
      };
      return map[dept] || '🏢';
    },
  },

  // Rich card generators
  cards: {
    statCard: (icon, title, value, trend = null, color = '#3b82f6') => `
      <div class="stat-card" style="border-left: 4px solid ${color};">
        <div class="stat-icon">${icon}</div>
        <div class="stat-info">
          <div class="stat-title">${title}</div>
          <div class="stat-value">${value}</div>
          ${trend ? `<div class="stat-trend" style="color:${trend > 0 ? '#10b981' : '#ef4444'};">
            ${trend > 0 ? '↑' : '↓'} ${Math.abs(trend)}%
          </div>` : ''}
        </div>
      </div>
    `,

    statusBadge: (status, size = 'md') => {
      const { emoji, color, bg } = ContentEnhancer.emoji.getStatusEmoji(status);
      const sizeClass = size === 'sm' ? 'text-xs px-2 py-1' : size === 'lg' ? 'text-lg px-3 py-2' : 'text-sm px-2 py-1';
      return `
        <span class="badge ${sizeClass}" style="background:${bg};color:${color};border-radius:20px;font-weight:600;display:inline-flex;align-items:center;gap:4px;">
          ${emoji} ${status}
        </span>
      `;
    },

    alertBanner: (type, message, icon = null) => {
      const colors = {
        'warning': { bg: '#fef3c7', border: '#fcd34d', text: '#92400e', icon: '⚠️' },
        'error': { bg: '#fee2e2', border: '#fca5a5', text: '#991b1b', icon: '❌' },
        'success': { bg: '#d1fae5', border: '#6ee7b7', text: '#065f46', icon: '✅' },
        'info': { bg: '#dbeafe', border: '#93c5fd', text: '#1e40af', icon: 'ℹ️' },
      };
      const config = colors[type] || colors['info'];
      return `
        <div style="background:${config.bg};border:1px solid ${config.border};border-radius:8px;padding:12px 16px;margin-bottom:16px;display:flex;gap:12px;align-items:flex-start;color:${config.text};">
          <span style="font-size:20px;flex-shrink:0;">${icon || config.icon}</span>
          <div style="flex:1;">${message}</div>
        </div>
      `;
    },

    progressBar: (value, max = 100, label = '') => {
      const percent = Math.round((value / max) * 100);
      const color = percent < 50 ? '#10b981' : percent < 75 ? '#f59e0b' : '#ef4444';
      return `
        <div class="progress-container">
          <div style="display:flex;justify-content:space-between;margin-bottom:8px;font-size:12px;">
            <span>${label}</span>
            <span style="font-weight:600;color:${color};">${percent}%</span>
          </div>
          <div style="background:#e5e7eb;border-radius:10px;height:8px;overflow:hidden;">
            <div style="background:${color};height:100%;width:${percent}%;transition:width 0.3s ease;border-radius:10px;"></div>
          </div>
        </div>
      `;
    },

    glowingCard: (title, content, icon = '✨') => `
      <div class="glowing-card">
        <div class="card-glow"></div>
        <div class="card-icon">${icon}</div>
        <div class="card-title">${title}</div>
        <div class="card-content">${content}</div>
      </div>
    `,
  },

  // Dynamic greeting and welcome messages
  greeting: {
    getWelcomeMessage: (name = 'User', role = '') => {
      const { emoji, text } = ContentEnhancer.emoji.getTimeGreeting();
      const roleMsg = role ? `, ${role}` : '';
      const messages = [
        `${emoji} ${text}, ${name}${roleMsg}! 👋`,
        `${emoji} Welcome back, ${name}! Ready to make an impact?`,
        `${emoji} Hi ${name}! Let's make today count! 💪`,
        `${emoji} ${text}, ${name}! Let's dive in! 🚀`,
      ];
      return messages[Math.floor(Math.random() * messages.length)];
    },

    getMessageOfDay: () => {
      const messages = [
        '🎯 Focus on what matters most today',
        '💡 Every action has a purpose',
        '🌟 You\'re doing amazing, keep it up!',
        '⚡ Efficiency is the key to success',
        '🚀 Let\'s make progress today',
        '💼 Teamwork makes the dream work',
        '📈 Growth happens one day at a time',
        '✨ Excellence is in the details',
      ];
      return messages[Math.floor(Math.random() * messages.length)];
    },
  },

  // Animate elements
  animate: {
    pulse: (element) => {
      element.style.animation = 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite';
    },
    shimmer: (element) => {
      element.style.animation = 'shimmer 2s infinite';
    },
    bounce: (element) => {
      element.style.animation = 'bounce 0.6s ease-in-out';
    },
  },

  // Format utilities
  format: {
    currency: (value, currency = '$') => {
      return currency + new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(value);
    },
    percentage: (value) => `${value.toFixed(1)}%`,
    number: (value) => new Intl.NumberFormat('en-US').format(value),
  },
};

// Add CSS animations if not already present
if (!document.getElementById('content-enhancer-styles')) {
  const style = document.createElement('style');
  style.id = 'content-enhancer-styles';
  style.innerHTML = `
    /* Stat Card */
    .stat-card {
      background: white;
      border-radius: 12px;
      padding: 20px;
      display: flex;
      gap: 16px;
      align-items: center;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      transition: all 0.3s ease;
      cursor: pointer;
    }
    .stat-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 16px rgba(0,0,0,0.12);
    }
    .stat-icon {
      font-size: 32px;
      flex-shrink: 0;
    }
    .stat-info {
      flex: 1;
    }
    .stat-title {
      font-size: 12px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 4px;
    }
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #1f2937;
    }
    .stat-trend {
      font-size: 12px;
      margin-top: 4px;
      font-weight: 600;
    }

    /* Glowing Card */
    .glowing-card {
      position: relative;
      background: white;
      border-radius: 12px;
      padding: 24px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0,0,0,0.08);
    }
    .card-glow {
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200%;
      height: 200%;
      background: radial-gradient(circle, rgba(59,130,246,0.1) 0%, transparent 70%);
      animation: glow-rotate 8s linear infinite;
    }
    .card-icon {
      font-size: 40px;
      margin-bottom: 12px;
      position: relative;
      z-index: 1;
    }
    .card-title {
      font-size: 14px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      position: relative;
      z-index: 1;
    }
    .card-content {
      font-size: 18px;
      font-weight: 600;
      color: #1f2937;
      position: relative;
      z-index: 1;
    }

    /* Animations */
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    @keyframes shimmer {
      0% { background-position: -1000px 0; }
      100% { background-position: 1000px 0; }
    }
    @keyframes bounce {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-10px); }
    }
    @keyframes glow-rotate {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }

    /* Progress Container */
    .progress-container {
      margin: 12px 0;
    }

    /* Badge */
    .badge {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
  `;
  document.head.appendChild(style);
}
