// resistencia: qolqe atiende de 6:00 a 24:00 sin reinicios.
// la carga de hora punta durante una hora completa, para ver si la memoria o los tiempos crecen
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: {
    resistencia: {
      executor: 'ramping-vus',
      stages: [
        { duration: '2m', target: 100 },
        { duration: '60m', target: 100 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '2m',
    },
  },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
