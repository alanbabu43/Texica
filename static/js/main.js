// Main JS file for TEXICA

// Initialize Map
function initMap(mapId, pickupId, dropoffId, editable = false) {
    var map = L.map(mapId).setView([20.5937, 78.9629], 5); // Default to India

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    var pickupMarker, dropoffMarker;

    // Custom icons
    var pickupIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    var dropoffIcon = L.icon({
        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
        shadowSize: [41, 41]
    });

    if (editable) {
        map.on('click', function (e) {
            if (!pickupMarker) {
                pickupMarker = L.marker(e.latlng, { icon: pickupIcon, draggable: true }).addTo(map);
                updateCoords(e.latlng, 'pickup');

                pickupMarker.on('dragend', function (event) {
                    updateCoords(event.target.getLatLng(), 'pickup');
                });
            } else if (!dropoffMarker) {
                dropoffMarker = L.marker(e.latlng, { icon: dropoffIcon, draggable: true }).addTo(map);
                updateCoords(e.latlng, 'dropoff');

                dropoffMarker.on('dragend', function (event) {
                    updateCoords(event.target.getLatLng(), 'dropoff');
                });

                // Zoom to fit both markers
                var group = new L.featureGroup([pickupMarker, dropoffMarker]);
                map.fitBounds(group.getBounds().pad(0.1));
            } else {
                // Reset markers if both exist
                map.removeLayer(pickupMarker);
                map.removeLayer(dropoffMarker);
                pickupMarker = null;
                dropoffMarker = null;
                document.getElementById('pickup-lat').value = '';
                document.getElementById('pickup-lng').value = '';
                document.getElementById('dropoff-lat').value = '';
                document.getElementById('dropoff-lng').value = '';
            }
        });
    }

    async function updateCoords(latlng, type) {
        document.getElementById(type + '-lat').value = latlng.lat.toFixed(6);
        document.getElementById(type + '-lng').value = latlng.lng.toFixed(6);

        var locInput = document.getElementById(type + '-location');
        if (locInput) {
            locInput.value = "Fetching address...";
            var address = await reverseGeocode(latlng.lat, latlng.lng);
            if (address) {
                locInput.value = address;
            } else {
                locInput.value = "Location (" + latlng.lat.toFixed(4) + ", " + latlng.lng.toFixed(4) + ")";
            }
        }
    }

    return map;
}

// Reverse Geocode (Coords -> Address)
async function reverseGeocode(lat, lng) {
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
            headers: {
                'User-Agent': 'TexicaTaxiApp/1.0'
            }
        });
        const data = await response.json();
        return data.display_name; // Full address
    } catch (error) {
        console.error("Reverse geocoding failed:", error);
        return null;
    }
}

// Display-only map for ride tracking
// Geocode address using Nominatim
async function geocodeAddress(address) {
    if (!address) return null;
    try {
        const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`, {
            headers: {
                'User-Agent': 'TexicaTaxiApp/1.0'
            }
        });
        const data = await response.json();
        if (data && data.length > 0) {
            return {
                lat: parseFloat(data[0].lat),
                lng: parseFloat(data[0].lon),
                display_name: data[0].display_name
            };
        }
    } catch (error) {
        console.error("Geocoding failed for:", address, error);
    }
    return null;
}

// Display-only map for ride tracking
async function showRideMap(mapId, pLat, pLng, dLat, dLng, pAddr, dAddr) {
    var mapContainer = document.getElementById(mapId);

    // Check if we have valid coordinates
    var hasPickup = pLat && pLng && pLat !== 'None' && pLng !== 'None';
    var hasDropoff = dLat && dLng && dLat !== 'None' && dLng !== 'None';

    var pickupCoords = hasPickup ? { lat: parseFloat(pLat), lng: parseFloat(pLng) } : null;
    var dropoffCoords = hasDropoff ? { lat: parseFloat(dLat), lng: parseFloat(dLng) } : null;

    // If missing coordinates, try to geocode
    if (!pickupCoords && pAddr) {
        console.log("Geocoding pickup address:", pAddr);
        mapContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 bg-light"><div class="spinner-border text-primary me-2" role="status"></div><span class="text-muted">Locating Pickup...</span></div>';
        pickupCoords = await geocodeAddress(pAddr);
    }

    if (!dropoffCoords && dAddr) {
        console.log("Geocoding dropoff address:", dAddr);
        if (mapContainer.innerHTML.includes('Locating')) {
            mapContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 bg-light"><div class="spinner-border text-primary me-2" role="status"></div><span class="text-muted">Locating Dropoff...</span></div>';
        }
        dropoffCoords = await geocodeAddress(dAddr);
    }

    // Final check
    if (!pickupCoords || !dropoffCoords) {
        console.error("Could not resolve coordinates for map.");
        mapContainer.innerHTML = '<div class="d-flex align-items-center justify-content-center h-100 bg-light text-muted">Map data unavailable for these locations</div>';
        return;
    }

    // Clear loading state
    mapContainer.innerHTML = '';

    var map = L.map(mapId);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    var pickup = [pickupCoords.lat, pickupCoords.lng];
    var dropoff = [dropoffCoords.lat, dropoffCoords.lng];

    var pMarker = L.marker(pickup, {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
            iconSize: [25, 41], iconAnchor: [12, 41]
        })
    }).addTo(map).bindPopup(pAddr || "Pickup Point");

    var dMarker = L.marker(dropoff, {
        icon: L.icon({
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
            iconSize: [25, 41], iconAnchor: [12, 41]
        })
    }).addTo(map).bindPopup(dAddr || "Dropoff Point");

    // Draw route or line
    if (typeof L.Routing !== 'undefined') {
        L.Routing.control({
            waypoints: [
                L.latLng(pickup[0], pickup[1]),
                L.latLng(dropoff[0], dropoff[1])
            ],
            routeWhileDragging: false,
            addWaypoints: false,
            draggableWaypoints: false,
            fitSelectedRoutes: true,
            show: false, // Hide itinerary
            lineOptions: {
                styles: [{ color: 'blue', opacity: 0.6, weight: 4 }]
            },
            createMarker: function () { return null; }
        }).on('routesfound', function (e) {
            var routes = e.routes;
            var summary = routes[0].summary;
            // totalDistance is in meters, round to 1 decimal place
            var totalDistance = (summary.totalDistance / 1000).toFixed(2);

            // Dispatch event for other scripts to listen
            var event = new CustomEvent('ride:route_found', {
                detail: {
                    distance_km: totalDistance
                }
            });
            document.getElementById(mapId).dispatchEvent(event);
        }).addTo(map);
    } else {
        // Fallback to straight line
        L.polyline([pickup, dropoff], { color: 'blue', weight: 4, opacity: 0.6 }).addTo(map);
        var group = new L.featureGroup([pMarker, dMarker]);
        map.fitBounds(group.getBounds().pad(0.2));
    }

    return map;
}

// Auto-dismiss alerts
document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function (alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});
