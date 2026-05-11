/**
 * Store-and-Forward Offline Queue (Art. 3 Local-First, Erkenntnis 11)
 */

import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { SensorPayload, CaptureResponse } from '../sensors/types';
import { sendCapture } from './api';
import { CONFIG } from '../config';

interface QueueEntry {
  id: string;
  payload: SensorPayload;
  enqueuedAt: string;
  retries: number;
}

async function loadQueue(): Promise<QueueEntry[]> {
  try {
    const raw = await AsyncStorage.getItem(CONFIG.QUEUE.STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

async function saveQueue(queue: QueueEntry[]): Promise<void> {
  await AsyncStorage.setItem(CONFIG.QUEUE.STORAGE_KEY, JSON.stringify(queue));
}

export async function enqueue(payload: SensorPayload): Promise<void> {
  const queue = await loadQueue();
  if (queue.length >= CONFIG.QUEUE.MAX_SIZE) queue.shift();
  queue.push({
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    payload,
    enqueuedAt: new Date().toISOString(),
    retries: 0,
  });
  await saveQueue(queue);
}

export async function flushQueue(): Promise<CaptureResponse[]> {
  const queue = await loadQueue();
  if (queue.length === 0) return [];
  const results: CaptureResponse[] = [];
  const remaining: QueueEntry[] = [];
  for (const entry of queue) {
    try {
      const response = await sendCapture(entry.payload);
      results.push(response);
    } catch {
      if (entry.retries < 5) {
        remaining.push({ ...entry, retries: entry.retries + 1 });
      }
    }
  }
  await saveQueue(remaining);
  return results;
}

export async function getQueueLength(): Promise<number> {
  const queue = await loadQueue();
  return queue.length;
}

export async function clearQueue(): Promise<void> {
  await AsyncStorage.removeItem(CONFIG.QUEUE.STORAGE_KEY);
}

export function startAutoFlush(
  onFlush?: (results: CaptureResponse[]) => void
): () => void {
  const unsubscribe = NetInfo.addEventListener(async (state) => {
    if (state.isConnected && state.isInternetReachable) {
      const results = await flushQueue();
      if (results.length > 0) onFlush?.(results);
    }
  });
  const intervalId = setInterval(async () => {
    const netState = await NetInfo.fetch();
    if (netState.isConnected && netState.isInternetReachable) {
      const results = await flushQueue();
      if (results.length > 0) onFlush?.(results);
    }
  }, CONFIG.QUEUE.FLUSH_INTERVAL_MS);
  return () => {
    unsubscribe();
    clearInterval(intervalId);
  };
}
