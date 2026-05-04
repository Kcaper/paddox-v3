import client from './client'

export const paddocksApi = {
  list: () => client.get('/api/paddocks/'),
  detail: (id) => client.get(`/api/paddocks/${id}/`),
  create: (data) => client.post('/api/paddocks/create/', data),
  join: (join_code) => client.post('/api/paddocks/join/', { join_code }),
  leaderboard: (paddockId) => client.get(`/api/leaderboards/${paddockId}/racely/`),
  seasonLeaderboard: (paddockId) => client.get(`/api/leaderboards/${paddockId}/season/`),
  raceLeaderboard: (paddockId, raceId) => client.get(`/api/leaderboards/${paddockId}/racely/${raceId}/`),
  predictions: (paddockId) => client.get(`/api/paddocks/${paddockId}/predictions/`),
  myScores: () => client.get('/api/leaderboards/me/'),
  updateMemberRole: (paddockId, userId, role) =>
    client.patch(`/api/paddocks/${paddockId}/members/${userId}/`, { role }),
  removeMember: (paddockId, userId) =>
    client.delete(`/api/paddocks/${paddockId}/members/${userId}/`),
}
