// sondeo previo al estres: sube sin pausas de 0 a 2000 usuarios en 20 minutos
// solo sirve para ubicar donde se rompe y elegir los escalones de estres.js
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: {
    sondeo: {
      executor: 'ramping-vus',
      stages: [
        { duration: '20m', target: 2000 },
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '1m',
    },
  },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
