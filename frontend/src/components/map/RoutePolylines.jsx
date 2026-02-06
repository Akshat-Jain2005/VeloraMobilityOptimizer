import { Polyline, Popup } from 'react-leaflet'

function formatTime(minutes) {
  if (!minutes && minutes !== 0) return '--'
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

export default function RoutePolylines({ routes }) {
  if (!routes || routes.length === 0) return null

  return (
    <>
      {routes.map((route, idx) => {
        if (!route.stops || route.stops.length < 2) return null

        // Create positions array from stops
        const positions = route.stops.map(stop => [stop.lat, stop.lon])

        return (
          <Polyline
            key={`route-${idx}`}
            positions={positions}
            color={route.color}
            weight={4}
            opacity={0.8}
          >
            <Popup>
              <div style={{ fontSize: '12px', minWidth: '150px' }}>
                <strong style={{ color: route.color }}>{route.vehicleId}</strong>
                <br />
                <strong>Stops:</strong> {route.stops.length}
                <hr style={{ margin: '4px 0', border: 'none', borderTop: '1px solid #eee' }} />
                {route.stops.map((stop, sIdx) => (
                  <div key={sIdx} style={{ marginBottom: '2px' }}>
                    {stop.type === 'pickup' ? '🟢' : '🔴'} {stop.employeeId} @ {formatTime(stop.arrivalTime)}
                  </div>
                ))}
              </div>
            </Popup>
          </Polyline>
        )
      })}
    </>
  )
}
