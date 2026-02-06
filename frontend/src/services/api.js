import axios from 'axios'

const API_BASE = '/api'

const api = axios.create({
  baseURL: API_BASE
})

export async function uploadFile(file) {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/optimize', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
  return response.data
}

export async function getJobStatus(jobId) {
  const response = await api.get(`/optimize/${jobId}/status`)
  return response.data
}

export async function getJobResult(jobId) {
  const response = await api.get(`/optimize/${jobId}/result`)
  return response.data
}

export async function getTestCases() {
  const response = await api.get('/testcases')
  return response.data
}

export async function runTestCase(id) {
  const response = await api.post(`/testcases/${id}/run`)
  return response.data
}
