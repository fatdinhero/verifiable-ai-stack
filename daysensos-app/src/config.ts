/**
 * DaySensOS App Configuration
 * Server-Verbindung zum Mac Mini M4 (L4-L5 Pipeline).
 */

export const CONFIG = {
  SERVER_URL: 'http://192.168.5.164:8111',
  CAPTURE_ENDPOINT: '/capture',
  SENSOR_INTERVALS: {
    gps: 60_000,
    accelerometer: 1_000,
    light: 30_000,
    bt_scan: 120_000,
    screen_time: 300_000,
    clock: 1_000,
  },
  QUEUE: {
    MAX_SIZE: 500,
    FLUSH_INTERVAL_MS: 30_000,
    STORAGE_KEY: '@daysensos/offline_queue',
  },
  CONSENT_STORAGE_KEY: '@daysensos/consent',
  DAYSCORE_STORAGE_KEY: '@daysensos/dayscore',
  SERVER_URL_STORAGE_KEY: '@daysensos/server_url',
} as const;
