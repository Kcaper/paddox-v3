import client from './client'

export const predictionsApi = {
  racelyCurrentState: () => client.get('/api/predictions/racely/current/'),
  submitRacely: (driverPositions, poleDriverId, flDriverId) =>
    client.post('/api/predictions/racely/submit/', {
      driver_positions: driverPositions,
      pole_driver_id: poleDriverId,
      fastest_lap_driver_id: flDriverId,
    }),
}
