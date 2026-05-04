import client from './client'

export const f1Api = {
  season: () => client.get('/api/f1/season/'),
  races: () => client.get('/api/f1/races/'),
  race: (id) => client.get(`/api/f1/races/${id}/`),
  drivers: (onGrid = true) => client.get(`/api/f1/drivers/?on_grid=${onGrid}`),
  constructors: () => client.get('/api/f1/constructors/'),
  driverStandings: () => client.get('/api/f1/standings/drivers/'),
  constructorStandings: () => client.get('/api/f1/standings/constructors/'),
}
