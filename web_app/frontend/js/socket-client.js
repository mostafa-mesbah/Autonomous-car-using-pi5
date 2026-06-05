/* socket-client.js — shared WebSocket + API client */
/* SERVER_URL is declared by each page individually to avoid redeclaration errors */
if (typeof SERVER_URL === 'undefined') {
  window.SERVER_URL = `http://${window.location.hostname}:5000`;
}

const socket = io(window.SERVER_URL || SERVER_URL, {
  transports: ['websocket', 'polling'],
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionAttempts: 20
});

socket.on('connect',    () => updateConnUI(true));
socket.on('disconnect', () => updateConnUI(false));
socket.on('error', e => console.error('Socket error:', e));

function updateConnUI(ok) {
  /* update any conn-pill elements on the page */
  document.querySelectorAll('.conn-pill').forEach(el => {
    el.className = 'conn-pill ' + (ok ? 'ok' : 'bad');
    el.textContent = ok ? 'Connected' : 'Disconnected';
  });
  /* legacy support for older pages */
  const s = document.getElementById('connectionStatus');
  if (s) {
    s.textContent = ok ? 'Connected' : 'Disconnected';
    s.className = 'connection-status ' + (ok ? 'connected' : 'disconnected');
  }
}

window.socketAPI = {
  selectCar:      (id)         => socket.emit('select_car',      { car_id: id }),
  setDestination: (id, la, lo) => socket.emit('set_destination', { car_id: id, lat: la, lon: lo }),
  emergencyStop:  (id)         => { if (confirm(`EMERGENCY STOP ${id}?`)) socket.emit('emergency_stop', { car_id: id }) },
  changeMode:     (id, mode)   => socket.emit('change_mode',     { car_id: id, mode }),
  endTrip:        (id)         => socket.emit('end_trip',         { car_id: id }),
  clearAlerts:    (id)         => socket.emit('clear_alerts',     { car_id: id }),
};
