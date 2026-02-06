function formatTime(minutes) {
  if (!minutes && minutes !== 0) return '--'
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

export default function RouteDetails({ routes, mapData }) {
  if (!routes) return null

  const activeRoutes = routes.filter(r => r.stops && r.stops.length > 0)

  if (activeRoutes.length === 0) {
    return (
      <div className="empty-state">
        <p>No active routes</p>
      </div>
    )
  }

  return (
    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
      {activeRoutes.map((route, idx) => {
        const routeInfo = mapData?.routes?.find(r => r.vehicleId === route.vehicleIdStr)
        const color = routeInfo?.color || '#667eea'

        // Count unique employees
        const employees = [...new Set(route.stops.map(s => s.employeeId))]

        return (
          <div
            key={idx}
            className="route-card"
            style={{ borderColor: color, background: `${color}10` }}
          >
            <div className="route-header">
              <span className="route-title" style={{ color }}>
                {route.vehicleIdStr}
              </span>
              <span className="route-stats">
                {route.totalDist?.toFixed(1)} km | {Math.round(route.totalTime)} min
              </span>
            </div>
            <div className="route-stops">
              <strong>Employees:</strong> {employees.join(', ')}
            </div>
            <div className="route-stops" style={{ marginTop: '4px' }}>
              {route.stops.slice(0, 6).map((stop, sIdx) => (
                <span key={sIdx} style={{ marginRight: '6px' }}>
                  {stop.type === 'pickup' ? '🟢' : '🔴'}
                  <small>{stop.employeeId}</small>
                </span>
              ))}
              {route.stops.length > 6 && (
                <span style={{ color: '#666' }}>+{route.stops.length - 6} more</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
