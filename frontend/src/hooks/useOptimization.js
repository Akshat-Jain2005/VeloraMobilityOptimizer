import { useCallback, useRef, useEffect } from 'react'
import { useOptimizationContext } from '../context/OptimizationContext'
import { uploadFile, runTestCase, getJobStatus, getJobResult, getTestCases } from '../services/api'

export function useOptimization() {
  const { state, dispatch } = useOptimizationContext()
  const pollIntervalRef = useRef(null)

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current)
      }
    }
  }, [])

  // Poll job status
  const startPolling = useCallback((jobId) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }

    pollIntervalRef.current = setInterval(async () => {
      try {
        const status = await getJobStatus(jobId)

        dispatch({
          type: 'UPDATE_PROGRESS',
          payload: { stage: status.stage, progress: status.progress }
        })

        if (status.status === 'complete') {
          clearInterval(pollIntervalRef.current)
          const result = await getJobResult(jobId)
          dispatch({ type: 'SET_RESULTS', payload: result })
        } else if (status.status === 'error') {
          clearInterval(pollIntervalRef.current)
          dispatch({ type: 'SET_ERROR', payload: status.error })
        }
      } catch (error) {
        clearInterval(pollIntervalRef.current)
        dispatch({ type: 'SET_ERROR', payload: error.message })
      }
    }, 500)
  }, [dispatch])

  // Upload file and start optimization
  const uploadAndOptimize = useCallback(async (file) => {
    try {
      dispatch({ type: 'RESET' })
      dispatch({ type: 'SET_STATUS', payload: 'uploading' })

      const response = await uploadFile(file)
      dispatch({ type: 'SET_JOB', payload: { jobId: response.jobId } })

      startPolling(response.jobId)
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
    }
  }, [dispatch, startPolling])

  // Run test case
  const runTest = useCallback(async (testCaseId) => {
    try {
      dispatch({ type: 'RESET' })
      dispatch({ type: 'SET_STATUS', payload: 'processing' })

      const response = await runTestCase(testCaseId)
      dispatch({ type: 'SET_JOB', payload: { jobId: response.jobId } })

      startPolling(response.jobId)
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message })
    }
  }, [dispatch, startPolling])

  // Load test cases
  const loadTestCases = useCallback(async () => {
    try {
      const response = await getTestCases()
      dispatch({ type: 'SET_TESTCASES', payload: response.testCases })
    } catch (error) {
      console.error('Failed to load test cases:', error)
    }
  }, [dispatch])

  // Set view mode
  const setViewMode = useCallback((mode) => {
    dispatch({ type: 'SET_VIEW_MODE', payload: mode })
  }, [dispatch])

  // Toggle vehicle selection
  const toggleVehicle = useCallback((vehicleId) => {
    dispatch({ type: 'TOGGLE_VEHICLE', payload: vehicleId })
  }, [dispatch])

  // Reset
  const reset = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current)
    }
    dispatch({ type: 'RESET' })
  }, [dispatch])

  return {
    ...state,
    uploadAndOptimize,
    runTest,
    loadTestCases,
    setViewMode,
    toggleVehicle,
    reset
  }
}
