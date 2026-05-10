/**
 * DaySensOS API Client — POST /capture an Mac Mini M4
 */

import { SensorPayload, CaptureResponse } from '../sensors/types';
import { CONFIG } from '../config';
import AsyncStorage from '@react-native-async-storage/async-storage';

async function getServerUrl(): Promise<string> {
  const stored = await AsyncStorage.getItem(CONFIG.SERVER_URL_STORAGE_KEY);
  return stored ?? CONFIG.SERVER_URL;
}

export async function setServerUrl(url: string): Promise<void> {
  await AsyncStorage.setItem(CONFIG.SERVER_URL_STORAGE_KEY, url);
}

export async function resetServerUrl(): Promise<void> {
  await AsyncStorage.removeItem(CONFIG.SERVER_URL_STORAGE_KEY);
}

export async function sendCapture(
  payload: SensorPayload
): Promise<CaptureResponse> {
  const baseUrl = await getServerUrl();
  const url = `${baseUrl}${CONFIG.CAPTURE_ENDPOINT}`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new Error(`Server returned ${response.status}: ${response.statusText}`);
  }
  return response.json();
}

export async function checkServerHealth(): Promise<boolean> {
  try {
    const baseUrl = await getServerUrl();
    const response = await fetch(`${baseUrl}/status`, {
      method: 'GET',
      signal: AbortSignal.timeout(5_000),
    });
    return response.ok;
  } catch {
    return false;
  }
}
