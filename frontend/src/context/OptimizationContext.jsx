import { createContext, useReducer, useContext } from 'react'

const OptimizationContext = createContext(null)

const initialState = {
  status: 'idle', // idle | uploading | processing | complete | error
  jobId: null,
  stage: null,
  progress: 0,
  results: null,
  viewMode: 'initial', // initial | optimized
  selectedVehicles: [], // empty = all selected
  error: null,
  testCases: []
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_STATUS':
      return { ...state, status: action.payload }
    case 'SET_JOB':
      return {
        ...state,
        jobId: action.payload.jobId,
        status: 'processing',
        stage: 'queued',
        progress: 0
      }
    case 'UPDATE_PROGRESS':
      return {
        ...state,
        stage: action.payload.stage,
        progress: action.payload.progress
      }
    case 'SET_RESULTS':
      return {
        ...state,
        status: 'complete',
        results: action.payload,
        viewMode: 'optimized'
      }
    case 'SET_ERROR':
      return {
        ...state,
        status: 'error',
        error: action.payload
      }
    case 'SET_VIEW_MODE':
      return { ...state, viewMode: action.payload }
    case 'TOGGLE_VEHICLE':
      const vehicleId = action.payload
      const selected = state.selectedVehicles.includes(vehicleId)
        ? state.selectedVehicles.filter(v => v !== vehicleId)
        : [...state.selectedVehicles, vehicleId]
      return { ...state, selectedVehicles: selected }
    case 'SELECT_ALL_VEHICLES':
      return { ...state, selectedVehicles: [] }
    case 'SET_TESTCASES':
      return { ...state, testCases: action.payload }
    case 'RESET':
      return { ...initialState, testCases: state.testCases }
    default:
      return state
  }
}

export function OptimizationProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState)

  return (
    <OptimizationContext.Provider value={{ state, dispatch }}>
      {children}
    </OptimizationContext.Provider>
  )
}

export function useOptimizationContext() {
  const context = useContext(OptimizationContext)
  if (!context) {
    throw new Error('useOptimizationContext must be used within OptimizationProvider')
  }
  return context
}
