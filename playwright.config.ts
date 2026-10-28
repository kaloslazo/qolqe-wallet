import { defineConfig } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  features: 'features/*.feature',
  steps: 'tests/api-playwright/*.ts',
});

const PUERTO = process.env.QOLQE_PUERTO ?? '8000';
const PYTHON = process.env.PYTHON ?? (process.platform === 'win32' ? '.venv\\Scripts\\python' : '.venv/bin/python');

export default defineConfig({
  testDir,
  // Los escenarios comparten una sola BD y un solo reloj: se ejecutan en serie.
  workers: 1,
  fullyParallel: false,
  // En CI: un test.only olvidado rompe el pipeline, y un escenario que falla y pasa al reintentar (flaky)
  // también: el quality gate pide investigarlo, no dejarlo pasar en verde.
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  failOnFlakyTests: !!process.env.CI,
  reporter: [['list'], ['html', { open: 'never' }], ['junit', { outputFile: 'reportes/junit-api.xml' }], ['json', { outputFile: 'reportes/resultados-api.json' }]],
  use: {
    baseURL: process.env.QOLQE_URL ?? `http://localhost:${PUERTO}`,
    extraHTTPHeaders: { 'Content-Type': 'application/json' },
  },
  webServer: process.env.QOLQE_URL
    ? undefined
    : {
        command: `${PYTHON} -m uvicorn qolqe.main:app --port ${PUERTO}`,
        url: `http://localhost:${PUERTO}/api/salud`,
        reuseExistingServer: true,
        timeout: 120_000,
        env: { QOLQE_MODO_PRUEBA: '1' },
      },
});
