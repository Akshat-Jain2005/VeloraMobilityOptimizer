export default function TestCaseSelector({ testCases, onSelect, disabled }) {
  if (!testCases || testCases.length === 0) {
    return (
      <p style={{ fontSize: '0.875rem', color: '#666' }}>
        Loading test cases...
      </p>
    )
  }

  return (
    <div className="testcase-grid">
      {testCases.map((tc) => (
        <button
          key={tc.id}
          className="testcase-btn"
          onClick={() => onSelect(tc.id)}
          disabled={disabled}
          title={`${tc.employeeCount} employees, ${tc.vehicleCount} vehicles`}
        >
          {tc.name}
          <span className="testcase-info">
            {tc.employeeCount}E / {tc.vehicleCount}V
          </span>
        </button>
      ))}
    </div>
  )
}
