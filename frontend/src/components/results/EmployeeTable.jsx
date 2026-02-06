function formatTime(minutes) {
  if (!minutes && minutes !== 0) return '--'
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`
}

function formatCurrency(value) {
  if (!value && value !== 0) return '--'
  return `₹${Math.round(value)}`
}

export default function EmployeeTable({ assignments }) {
  if (!assignments || assignments.length === 0) {
    return (
      <div className="empty-state">
        <p>No employee assignments</p>
      </div>
    )
  }

  // Sort by employee ID
  const sorted = [...assignments].sort((a, b) =>
    a.employeeId.localeCompare(b.employeeId, undefined, { numeric: true })
  )

  return (
    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
      <table className="employee-table">
        <thead>
          <tr>
            <th>Employee</th>
            <th>Vehicle</th>
            <th>Pickup</th>
            <th>Dropoff</th>
            <th>Baseline</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((emp, idx) => (
            <tr key={idx}>
              <td>
                <strong>{emp.employeeId}</strong>
                <br />
                <small style={{ color: '#666' }}>P{emp.priority}</small>
              </td>
              <td>
                {emp.vehicleId ? (
                  <span
                    className="vehicle-badge"
                    style={{ background: emp.vehicleColor }}
                  >
                    {emp.vehicleId}
                  </span>
                ) : (
                  <span style={{ color: '#999' }}>--</span>
                )}
              </td>
              <td>{formatTime(emp.pickupTime)}</td>
              <td>{formatTime(emp.dropoffTime)}</td>
              <td>{formatCurrency(emp.baselineCost)}</td>
              <td>
                <span className={`status-badge ${emp.status}`}>
                  {emp.status}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
