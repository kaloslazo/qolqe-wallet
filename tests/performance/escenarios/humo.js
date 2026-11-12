// linea base: 1 usuario, sin competencia. sirve de referencia para comparar los tiempos
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

export const options = {
  scenarios: { humo: { executor: 'constant-vus', vus: 1, duration: '4m' } },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
