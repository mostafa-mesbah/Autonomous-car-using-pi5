/**
 * Notifications JavaScript
 * Handles browser notifications for critical alerts
 */

let notificationsEnabled = localStorage.getItem('notificationsEnabled') === 'true';

// Request notification permission
function requestNotificationPermission() {
    if (!('Notification' in window)) {
        alert('This browser does not support notifications');
        return;
    }

    if (Notification.permission === 'granted') {
        alert('Notifications are already enabled!');
        return;
    }

    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            notificationsEnabled = true;
            localStorage.setItem('notificationsEnabled', 'true');

            // Show test notification
            new Notification('Notifications Enabled', {
                body: 'You will now receive alerts from the car monitoring system',
                icon: '🚗',
                tag: 'test'
            });

            if (document.getElementById('notificationsEnabled')) {
                document.getElementById('notificationsEnabled').checked = true;
            }
        } else {
            alert('Notification permission denied');
        }
    });
}

// Show browser notification
function notifyUser(message, severity = 'info') {
    if (!notificationsEnabled || Notification.permission !== 'granted') {
        return;
    }

    const icons = {
        info: 'ℹ️',
        warning: '⚠️',
        critical: '🚨'
    };

    const titles = {
        info: 'Car Alert',
        warning: 'Car Warning',
        critical: 'CRITICAL ALERT'
    };

    const notification = new Notification(titles[severity], {
        body: message,
        icon: icons[severity],
        tag: severity + '-' + Date.now(),
        requireInteraction: severity === 'critical'
    });

    // Play sound for critical alerts
    if (severity === 'critical') {
        playAlertSound();
    }

    // Auto close after 10 seconds for non-critical
    if (severity !== 'critical') {
        setTimeout(() => notification.close(), 10000);
    }

    notification.onclick = () => {
        window.focus();
        notification.close();
    };
}

// Play alert sound (simple beep using Web Audio API)
function playAlertSound() {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.value = 800;
    oscillator.type = 'sine';

    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.5);
}

// Initialize notification settings
document.addEventListener('DOMContentLoaded', () => {
    const notifCheckbox = document.getElementById('notificationsEnabled');
    const requestBtn = document.getElementById('requestPermissionBtn');

    if (notifCheckbox) {
        notifCheckbox.checked = notificationsEnabled;

        notifCheckbox.addEventListener('change', (e) => {
            if (e.target.checked) {
                if (Notification.permission !== 'granted') {
                    requestNotificationPermission();
                } else {
                    notificationsEnabled = true;
                    localStorage.setItem('notificationsEnabled', 'true');
                }
            } else {
                notificationsEnabled = false;
                localStorage.setItem('notificationsEnabled', 'false');
            }
        });
    }

    if (requestBtn) {
        requestBtn.addEventListener('click', requestNotificationPermission);

        // Hide button if already granted
        if (Notification.permission === 'granted') {
            requestBtn.style.display = 'none';
        }
    }
});

// Listen for critical alerts from socket
socket.on('critical_alert', (data) => {
    notifyUser(data.alert.message, 'critical');
});

// Export for use in other scripts
window.notifyUser = notifyUser;
window.requestNotificationPermission = requestNotificationPermission;
