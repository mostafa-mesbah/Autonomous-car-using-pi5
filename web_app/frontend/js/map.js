/**
 * Map JavaScript
 * Handles Leaflet map, car tracking, and destination setting
 */

let selectedCar = localStorage.getItem('selectedCar');
let map = null;
let carMarker = null;
let destinationMarker = null;
let pathPolyline = null;
let pathCoordinates = [];

// Initialize map
function initMap() {
    // Create map centered on Cairo, Egypt
    map = L.map('map').setView([30.0444, 31.2357], 13);

    // Add OpenStreetMap tiles
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 19
    }).addTo(map);

    // Create custom car icon
    const carIcon = L.divIcon({
        className: 'custom-car-marker',
        html: '<div style="font-size: 30px; text-align: center;">🚗</div>',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });

    // Initialize car marker
    carMarker = L.marker([30.0444, 31.2357], { icon: carIcon }).addTo(map);
    carMarker.bindPopup('<b>Car Position</b><br>Waiting for data...');

    // Initialize path polyline
    pathPolyline = L.polyline([], { color: '#3b82f6', weight: 4 }).addTo(map);

    // Click handler for setting destination
    map.on('click', (e) => {
        if (selectedCar) {
            setDestinationOnMap(e.latlng.lat, e.latlng.lng);
        } else {
            alert('Please select a car first');
        }
    });
}

function setDestinationOnMap(lat, lng) {
    // Confirm with user
    if (!confirm(`Set destination to:\nLat: ${lat.toFixed(4)}\nLon: ${lng.toFixed(4)}`)) {
        return;
    }

    // Remove old destination marker
    if (destinationMarker) {
        map.removeLayer(destinationMarker);
    }

    // Add new destination marker
    destinationMarker = L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'custom-destination-marker',
            html: '<div style="font-size: 30px; text-align: center;">📍</div>',
            iconSize: [40, 40],
            iconAnchor: [20, 40]
        })
    }).addTo(map);

    destinationMarker.bindPopup('<b>Destination</b>').openPopup();

    // Send to backend
    socketAPI.setDestination(selectedCar, lat, lng);
}

function updateCarPosition(carState) {
    if (!carState || !carState.gps) return;

    const { lat, lon } = carState.gps;

    // Update car marker position
    carMarker.setLatLng([lat, lon]);
    carMarker.setPopupContent(`
        <b>${carState.car_id}</b><br>
        Speed: ${carState.speed} km/h<br>
        Battery: ${carState.battery}%<br>
        Status: ${carState.status}
    `);

    // Add to path if car is moving
    if (carState.speed > 0) {
        pathCoordinates.push([lat, lon]);

        // Keep only last 200 points
        if (pathCoordinates.length > 200) {
            pathCoordinates.shift();
        }

        pathPolyline.setLatLngs(pathCoordinates);
    }

    // Update destination marker if set
    if (carState.destination && !destinationMarker) {
        destinationMarker = L.marker(
            [carState.destination.lat, carState.destination.lon],
            {
                icon: L.divIcon({
                    className: 'custom-destination-marker',
                    html: '<div style="font-size: 30px; text-align: center;">📍</div>',
                    iconSize: [40, 40],
                    iconAnchor: [20, 40]
                })
            }
        ).addTo(map);
        destinationMarker.bindPopup('<b>Destination</b>');
    }
}

// Load cars for selector
async function loadCars() {
    try {
        const response = await fetch(`${SERVER_URL}/api/cars`);
        const cars = await response.json();

        const selector = document.getElementById('carSelector');
        selector.innerHTML = '<option value="">Select Car...</option>';

        Object.keys(cars).forEach(carId => {
            const option = document.createElement('option');
            option.value = carId;
            option.textContent = carId;
            if (carId === selectedCar) option.selected = true;
            selector.appendChild(option);
        });

        // Load initial position
        if (selectedCar && cars[selectedCar]) {
            updateCarPosition(cars[selectedCar]);
            map.setView([cars[selectedCar].gps.lat, cars[selectedCar].gps.lon], 15);
        }
    } catch (error) {
        console.error('Error loading cars:', error);
    }
}

// Event listeners
document.getElementById('carSelector').addEventListener('change', (e) => {
    selectedCar = e.target.value;
    localStorage.setItem('selectedCar', selectedCar);

    // Clear path when switching cars
    pathCoordinates = [];
    pathPolyline.setLatLngs([]);

    if (destinationMarker) {
        map.removeLayer(destinationMarker);
        destinationMarker = null;
    }

    if (selectedCar) {
        socketAPI.selectCar(selectedCar);
    }
});

document.getElementById('clearPathBtn').addEventListener('click', () => {
    pathCoordinates = [];
    pathPolyline.setLatLngs([]);
});

// Socket event listeners
socket.on('telemetry_update', (data) => {
    if (selectedCar && data[selectedCar]) {
        updateCarPosition(data[selectedCar]);
    }
});

socket.on('destination_set', (data) => {
    if (data.car_id === selectedCar) {
        console.log('Destination confirmed by server:', data);
    }
});

socket.on('connect', () => {
    if (selectedCar) {
        socketAPI.selectCar(selectedCar);
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (!selectedCar) {
        if (confirm('No car selected. Go to car selection page?')) {
            window.location.href = 'index.html';
        }
    }

    initMap();
    loadCars();
});
