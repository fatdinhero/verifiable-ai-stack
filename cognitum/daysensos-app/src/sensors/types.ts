/**
 * DaySensOS Sensor Types
 * L1-Perception Spezifikation (8 Kanaele) + POST /capture API-Spec.
 */

export type SensorChannel =
  | 'camera' | 'microphone' | 'gps' | 'accelerometer'
  | 'light' | 'bt_scan' | 'screen_time' | 'clock';

export interface ConsentState {
  camera: boolean;
  microphone: boolean;
  gps: boolean;
  accelerometer: boolean;
  light: boolean;
  bt_scan: boolean;
  screen_time: boolean;
  clock: boolean;
}

export const DEFAULT_CONSENT: ConsentState = {
  camera: false,
  microphone: false,
  gps: true,
  accelerometer: true,
  light: true,
  bt_scan: true,
  screen_time: true,
  clock: true,
};

export interface GpsData {
  lat: number;
  lon: number;
  accuracy: number;
}

export interface AccelerometerData {
  x: number;
  y: number;
  z: number;
}

export interface SensorPayload {
  sensor_data: {
    gps: GpsData | null;
    accelerometer: AccelerometerData | null;
    light: number | null;
    bt_devices: string[];
    screen_time_min: number | null;
    timestamp: string;
    consent_state: ConsentState;
    camera_frame?: null;
    audio_spectrum?: number[];
  };
}

export interface CaptureResponse {
  focus_score: number;
  episode: string;
  nudge: string | null;
  display_ttl_ms: number;
}

export type SensorStatus = 'active' | 'disabled' | 'unavailable' | 'error';
