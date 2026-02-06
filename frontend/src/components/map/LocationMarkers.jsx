import { Marker, Popup } from 'react-leaflet'
import L from 'leaflet'

// Custom marker icons
const createIcon = (color, size = 24) => {
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background: ${color};
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 3px solid white;
      box-shadow: 0 2px 5px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2]
  })
}

const pickupIcon = createIcon('#22c55e') // Green
const dropoffIcon = createIcon('#ef4444') // Red
const vehicleIcon = createIcon('#3b82f6', 20) // Blue, smaller

function formatTime(minutes) {
  if (!minutes && minutes !== 0) return '--'
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

export default function LocationMarkers({
  pickupPoints,
  dropoffPoints,
  vehicleStarts,
  viewMode
}) {
  return (
    <>
      {/* Pickup Points - Green */}
      {pickupPoints?.map((point, idx) => (
        <Marker
          key={`pickup-${idx}`}
          position={[point.lat, point.lon]}
          icon={pickupIcon}
        >
          <Popup>
            <div style={{ fontSize: '12px' }}>
              <strong>Pickup: {point.employeeId}</strong>
              <br />
              Window: {formatTime(point.earlyTime)} - {formatTime(point.lateTime)}
              <br />
              <span style={{ color: '#666' }}>
                {point.lat.toFixed(4)}, {point.lon.toFixed(4)}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Dropoff Points - Red */}
      {dropoffPoints?.map((point, idx) => (
        <Marker
          key={`dropoff-${idx}`}
          position={[point.lat, point.lon]}
          icon={dropoffIcon}
        >
          <Popup>
            <div style={{ fontSize: '12px' }}>
              <strong>Dropoff: {point.employeeId}</strong>
              <br />
              <span style={{ color: '#666' }}>
                {point.lat.toFixed(4)}, {point.lon.toFixed(4)}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}

      {/* Vehicle Start Locations - Blue (only show in initial view) */}
      {viewMode === 'initial' && vehicleStarts?.map((vehicle, idx) => (
        <Marker
          key={`vehicle-${idx}`}
          position={[vehicle.lat, vehicle.lon]}
          icon={vehicleIcon}
        >
          <Popup>
            <div style={{ fontSize: '12px' }}>
              <strong>Vehicle: {vehicle.vehicleId}</strong>
              <br />
              Category: {vehicle.category || 'standard'}
              <br />
              <span style={{ color: '#666' }}>
                {vehicle.lat.toFixed(4)}, {vehicle.lon.toFixed(4)}
              </span>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  )
}
