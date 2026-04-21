import axios from 'axios'

// In dev: BASE_URL = '/' → baseURL = '/api'
// In prod: BASE_URL = '/runneradmin/' → baseURL = '/runneradmin/api'
const api = axios.create({
  baseURL: import.meta.env.BASE_URL + 'api',
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = import.meta.env.BASE_URL + 'login'
    }
    return Promise.reject(error)
  }
)

export default api
