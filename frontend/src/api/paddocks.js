import client from './client'

export const paddocksApi = {
  list: () => client.get('/api/paddocks/'),
  detail: (id) => client.get(`/api/paddocks/${id}/`),
  create: (data) => client.post('/api/paddocks/create/', data),
  join: (join_code) => client.post('/api/paddocks/join/', { join_code }),
  leaderboard: (paddockId) => client.get(`/api/leaderboards/${paddockId}/racely/`),
}
