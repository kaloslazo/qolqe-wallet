// carga: la hora punta (12:00 a 13:00)
// 3000 sesiones por hora x 2 min por sesion = 100 usuarios a la vez (ley de little)
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: {
    hora_punta: {
      executor: 'ramping-vus',
      stages: [
        { duration: '2m', target: 100 },  // subida: lo que dura una sesion
        { duration: '20m', target: 100 }, // estable: unas 1000 sesiones
        { duration: '1m', target: 0 },
      ],
      gracefulRampDown: '2m',
    },
  },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
