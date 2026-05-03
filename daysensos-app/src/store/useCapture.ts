/**
 * useCapture Hook — orchestriert Sensor-Read → API → Queue → Store
 */

import { useCallback, useEffect, useRef } from 'react';
import { useConsentStore } from '../consent/store';
import { useDayScoreStore } from '../store/dayScore';
import { collectSensorData } from '../sensors/collector';
import { sendCapture, checkServerHealth } from '../network/api';
import { enqueue, startAutoFlush, getQueueLength } from '../network/queue';
import { CONFIG } from '../config';

interface UseCaptureOptions {
  autoCapture?: boolean;
  intervalMs?: number;
}

export function useCapture(options: UseCaptureOptions = {}) {
  const { autoCapture = false, intervalMs = CONFIG.SENSOR_INTERVALS.gps } = options;
  const consent = useConsentStore((s) => s.consent);
  const updateFromCapture = useDayScoreStore((s) => s.updateFromCapture);
  const setServerOnline = useDayScoreStore((s) => s.setServerOnline);
  const setQueueLength = useDayScoreStore((s) => s.setQueueLength);
  const captureRef = useRef(false);

  const capture = useCallback(async () => {
    if (captureRef.current) return;
    captureRef.current = true;
    try {
      const payload = await collectSensorData(consent);
      try {
        const response = await sendCapture(payload);
        updateFromCapture(response);
        setServerOnline(true);
      } catch {
        await enqueue(payload);
        setServerOnline(false);
      }
      const qLen = await getQueueLength();
      setQueueLength(qLen);
    } finally {
      captureRef.current = false;
    }
  }, [consent, updateFromCapture, setServerOnline, setQueueLength]);

  const checkHealth = useCallback(async () => {
    const online = await checkServerHealth();
    setServerOnline(online);
    return online;
  }, [setServerOnline]);

  useEffect(() => {
    if (!autoCapture) return;
    const id = setInterval(capture, intervalMs);
    return () => clearInterval(id);
  }, [autoCapture, intervalMs, capture]);

  useEffect(() => {
    const cleanup = startAutoFlush((results) => {
      const last = results[results.length - 1];
      if (last) updateFromCapture(last);
    });
    return cleanup;
  }, [updateFromCapture]);

  return { capture, checkHealth };
}
