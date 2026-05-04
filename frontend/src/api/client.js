import axios from 'axios'

const client = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const cookie = document.cookie
    .split(';')
    .find((c) => c.trim().startsWith('csrftoken='))
  if (cookie) {
    config.headers['X-CSRFToken'] = cookie.split('=')[1]
  }
  return config
})

export default client
