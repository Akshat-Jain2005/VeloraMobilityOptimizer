export default function ResultsSummary({ summary, baseline }) {
  if (!summary) return null

  const formatCurrency = (value) => {
    return `₹${Math.round(value).toLocaleString()}`
  }

  const formatPercent = (value) => {
    return `${value.toFixed(1)}%`
  }

  const formatDistance = (km) => {
    return `${km.toFixed(1)} km`
  }

  const formatTime = (minutes) => {
    const hours = Math.floor(minutes / 60)
    const mins = Math.round(minutes % 60)
    if (hours > 0) {
      return `${hours}h ${mins}m`
    }
    return `${mins} min`
  }

  return (
    <div className="summary-grid">
      <div className="summary-item">
        <div className="summary-value cost">
          {formatCurrency(summary.totalCost)}
        </div>
        <div className="summary-label">Optimized Cost</div>
      </div>

      <div className="summary-item">
        <div className="summary-value">
          {formatCurrency(summary.baselineCost)}
        </div>
        <div className="summary-label">Baseline Cost</div>
      </div>

      <div className="summary-item">
        <div className="summary-value savings">
          {formatPercent(summary.savings)}
        </div>
        <div className="summary-label">Cost Savings</div>
      </div>

      <div className="summary-item">
        <div className="summary-value">
          {summary.vehiclesUsed} / {summary.totalVehicles}
        </div>
        <div className="summary-label">Vehicles Used</div>
      </div>

      <div className="summary-item">
        <div className="summary-value">
          {formatDistance(summary.totalDistance)}
        </div>
        <div className="summary-label">Total Distance</div>
      </div>

      <div className="summary-item">
        <div className="summary-value">
          {formatTime(summary.totalTime)}
        </div>
        <div className="summary-label">Total Time</div>
      </div>

      <div className="summary-item">
        <div className="summary-value">
          {summary.totalEmployees - summary.unassignedCount}
        </div>
        <div className="summary-label">Assigned</div>
      </div>

      <div className="summary-item">
        <div className="summary-value" style={{ color: summary.unassignedCount > 0 ? '#ef4444' : '#22c55e' }}>
          {summary.unassignedCount}
        </div>
        <div className="summary-label">Unassigned</div>
      </div>
    </div>
  )
}
