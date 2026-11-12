// pico: la campaña quincena qolqe (15 y fin de mes, 12:00 a 12:15)
// el triple de usuarios que en hora punta (300) y la mayoria entra en los primeros 5 minutos.
// antes y despues se deja la hora punta normal (100) para ver si el sistema se recupera
import { sesion } from '../sesion.js';
import { CAMPANA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: {
    campana: {
      executor: 'ramping-vus',
      stages: [
        { duration: '2m', target: 100 },  // hora punta normal
        { duration: '2m', target: 100 },
        { duration: '5m', target: 300 },  // 12:00 a 12:05: entra la mayoria
        { duration: '10m', target: 300 }, // 12:05 a 12:15
        { duration: '1m', target: 100 },  // fin de la campaña
        { duration: '4m', target: 100 },  // recuperacion
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '2m',
    },
  },
  thresholds: CAMPANA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
