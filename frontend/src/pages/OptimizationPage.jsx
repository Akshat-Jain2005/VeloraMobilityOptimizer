import { useEffect } from 'react'
import { useOptimization } from '../hooks/useOptimization'
import FileUploader from '../components/upload/FileUploader'
import TestCaseSelector from '../components/upload/TestCaseSelector'
import MapContainer from '../components/map/MapContainer'
import MapLegend from '../components/map/MapLegend'
import ResultsSummary from '../components/results/ResultsSummary'
import RouteDetails from '../components/results/RouteDetails'
import EmployeeTable from '../components/results/EmployeeTable'

export default function OptimizationPage() {
  const {
    status,
    stage,
    progress,
    results,
    viewMode,
    error,
    testCases,
    loadTestCases,
    uploadAndOptimize,
    runTest,
    setViewMode,
    reset
  } = useOptimization()

  useEffect(() => {
    loadTestCases()
  }, [loadTestCases])

  const isProcessing = status === 'uploading' || status === 'processing'

  return (
    <main className="main-content">
      <aside className="sidebar">
        {/* Upload Section */}
        <div className="card">
          <h2 className="card-title">Upload Data</h2>
          <FileUploader
            onUpload={uploadAndOptimize}
            disabled={isProcessing}
          />
        </div>

        {/* Test Cases */}
        <div className="card">
          <h2 className="card-title">Test Cases</h2>
          <TestCaseSelector
            testCases={testCases}
            onSelect={runTest}
            disabled={isProcessing}
          />
        </div>

        {/* Progress */}
        {isProcessing && (
          <div className="card">
            <h2 className="card-title">Progress</h2>
            <div className="progress-section">
              <div className="progress-bar-container">
                <div
                  className="progress-bar"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="progress-text">
                {stage === 'queued' && 'Queued...'}
                {stage === 'parsing' && 'Parsing Excel file...'}
                {stage === 'solving' && 'Running optimization solver...'}
                {stage === 'loading' && 'Loading results...'}
                {stage === 'transforming' && 'Preparing visualization...'}
              </p>
            </div>
          </div>
        )}

        {/* Error */}
        {status === 'error' && (
          <div className="card">
            <div className="error-message">
              <p><strong>Error:</strong> {error}</p>
              <button onClick={reset} style={{ marginTop: '0.5rem' }}>
                Try Again
              </button>
            </div>
          </div>
        )}

        {/* Results Summary */}
        {results && (
          <div className="card">
            <h2 className="card-title">Results Summary</h2>
            <ResultsSummary summary={results.summary} baseline={results.baseline} />
          </div>
        )}

        {/* Route Details */}
        {results && viewMode === 'optimized' && (
          <div className="card">
            <h2 className="card-title">Routes</h2>
            <RouteDetails routes={results.routes} mapData={results.mapData} />
          </div>
        )}
      </aside>

      <section className="map-section">
        {/* View Toggle */}
        {results && (
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'initial' ? 'active' : ''}`}
              onClick={() => setViewMode('initial')}
            >
              Initial State
            </button>
            <button
              className={`toggle-btn ${viewMode === 'optimized' ? 'active' : ''}`}
              onClick={() => setViewMode('optimized')}
            >
              Optimized Routes
            </button>
          </div>
        )}

        {/* Map */}
        <div className="map-container">
          <MapContainer
            mapData={results?.mapData}
            viewMode={viewMode}
          />
        </div>

        {/* Legend */}
        <MapLegend viewMode={viewMode} routes={results?.mapData?.routes} />

        {/* Employee Table */}
        {results && (
          <div className="card">
            <h2 className="card-title">Employee Assignments</h2>
            <EmployeeTable assignments={results.employeeAssignments} />
          </div>
        )}
      </section>
    </main>
  )
}
