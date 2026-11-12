// estres: "hasta cuantos usuarios simultaneos podemos crecer antes de dejar de cumplir".
// escalones desde la hora punta hasta pasar el quiebre que mostro el sondeo (unos 1100 vus).
// cada escalon: 1 min de subida y 3 min arriba (una sesion y media)
import { sesion } from '../sesion.js';
import { HORA_PUNTA, ESTADISTICAS } from '../umbrales.js';

const ESCALONES = [100, 300, 600, 800, 1000, 1200, 1400];

const stages = [];
for (const vus of ESCALONES) {
  stages.push({ duration: '1m', target: vus });
  stages.push({ duration: '3m', target: vus });
}
stages.push({ duration: '1m', target: 0 });

export const options = {
  scenarios: { escalones: { executor: 'ramping-vus', stages, gracefulRampDown: '1m' } },
  thresholds: HORA_PUNTA,
  summaryTrendStats: ESTADISTICAS,
};

export default sesion;
