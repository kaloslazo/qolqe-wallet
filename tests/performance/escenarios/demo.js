// version corta de la prueba de carga para la demo en vivo (unos 4 minutos)
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: {
    demo: {
      executor: 'ramping-vus',
      stages: [
        { duration: '1m', target: 100 },
        { duration: '2m30s', target: 100 },
        { duration: '30s', target: 0 },
      ],
    },
  },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
