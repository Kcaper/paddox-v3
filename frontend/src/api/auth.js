import client from './client'

export const authApi = {
  register: (email, username, password) =>
    client.post('/api/users/register/', { email, username, password }),

  login: (email, password) =>
    client.post('/api/users/login/', { email, password }),

  logout: () =>
    client.post('/api/users/logout/'),

  me: () =>
    client.get('/api/users/me/'),

  updateProfile: (data) =>
    client.patch('/api/users/me/update/', data),
}
