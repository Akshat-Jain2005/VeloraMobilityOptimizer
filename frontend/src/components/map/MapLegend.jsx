export default function MapLegend({ viewMode, routes }) {
  return (
    <div className="map-legend">
      <div className="legend-item">
        <span className="legend-marker" style={{ background: '#22c55e' }}></span>
        <span>Pickup</span>
      </div>
      <div className="legend-item">
        <span className="legend-marker" style={{ background: '#ef4444' }}></span>
        <span>Dropoff</span>
      </div>
      {viewMode === 'initial' && (
        <div className="legend-item">
          <span className="legend-marker" style={{ background: '#3b82f6' }}></span>
          <span>Vehicle</span>
        </div>
      )}
      {viewMode === 'optimized' && routes?.map((route, idx) => (
        <div key={idx} className="legend-item">
          <span className="legend-line" style={{ background: route.color }}></span>
          <span>{route.vehicleId}</span>
        </div>
      ))}
    </div>
  )
}
