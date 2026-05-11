/**
 * Sensor Collector — Orchestriert alle 8 Sensorkanäle
 * Liest nur Sensoren mit aktivem Consent (Art. 2).
 */

import * as Location from 'expo-location';
import { Accelerometer, LightSensor } from 'expo-sensors';
import { ConsentState, SensorPayload, GpsData, AccelerometerData } from './types';

async function readGps(): Promise<GpsData | null> {
  try {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status !== 'granted') return null;
    const loc = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.Balanced,
    });
    return {
      lat: loc.coords.latitude,
      lon: loc.coords.longitude,
      accuracy: loc.coords.accuracy ?? 0,
    };
  } catch {
    return null;
  }
}

async function readAccelerometer(): Promise<AccelerometerData | null> {
  try {
    const available = await Accelerometer.isAvailableAsync();
    if (!available) return null;
    return new Promise((resolve) => {
      const sub = Accelerometer.addListener((data) => {
        sub.remove();
        resolve({ x: data.x, y: data.y, z: data.z });
      });
      Accelerometer.setUpdateInterval(100);
      setTimeout(() => { sub.remove(); resolve(null); }, 2000);
    });
  } catch {
    return null;
  }
}

async function readLight(): Promise<number | null> {
  try {
    const available = await LightSensor.isAvailableAsync();
    if (!available) return null;
    return new Promise((resolve) => {
      const sub = LightSensor.addListener((data) => {
        sub.remove();
        resolve(data.illuminance);
      });
      LightSensor.setUpdateInterval(100);
      setTimeout(() => { sub.remove(); resolve(null); }, 2000);
    });
  } catch {
    return null;
  }
}

async function readBluetooth(): Promise<string[]> {
  // TODO Phase 2: react-native-ble-plx
  return [];
}

async function readScreenTime(): Promise<number | null> {
  // TODO Phase 2: Native Module
  return null;
}

export async function collectSensorData(
  consent: ConsentState
): Promise<SensorPayload> {
  const [gps, accel, light, btDevices, screenTime] = await Promise.all([
    consent.gps ? readGps() : Promise.resolve(null),
    consent.accelerometer ? readAccelerometer() : Promise.resolve(null),
    consent.light ? readLight() : Promise.resolve(null),
    consent.bt_scan ? readBluetooth() : Promise.resolve([]),
    consent.screen_time ? readScreenTime() : Promise.resolve(null),
  ]);
  return {
    sensor_data: {
      gps,
      accelerometer: accel,
      light,
      bt_devices: btDevices,
      screen_time_min: screenTime,
      timestamp: new Date().toISOString(),
      consent_state: consent,
    },
  };
}
