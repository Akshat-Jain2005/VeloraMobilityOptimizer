import { OptimizationProvider } from './context/OptimizationContext'
import OptimizationPage from './pages/OptimizationPage'

function App() {
  return (
    <OptimizationProvider>
      <div className="app">
        <header className="header">
          <h1>Velora Mobility Optimizer</h1>
          <p>Heterogeneous Vehicle Routing with Time Windows</p>
        </header>
        <OptimizationPage />
      </div>
    </OptimizationProvider>
  )
}

export default App
