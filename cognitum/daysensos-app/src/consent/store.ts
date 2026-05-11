/**
 * Consent Store — Per-Sensor Consent (Art. 2, Erkenntnis 10)
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ConsentState, DEFAULT_CONSENT, SensorChannel } from '../sensors/types';
import { CONFIG } from '../config';

interface ConsentStore {
  consent: ConsentState;
  setConsent: (channel: SensorChannel, enabled: boolean) => void;
  resetConsent: () => void;
  isConsentGiven: (channel: SensorChannel) => boolean;
}

export const useConsentStore = create<ConsentStore>()(
  persist(
    (set, get) => ({
      consent: { ...DEFAULT_CONSENT },
      setConsent: (channel: SensorChannel, enabled: boolean) => {
        if (channel === 'clock') return;
        set((state) => ({
          consent: { ...state.consent, [channel]: enabled },
        }));
      },
      resetConsent: () => set({ consent: { ...DEFAULT_CONSENT } }),
      isConsentGiven: (channel: SensorChannel) => get().consent[channel],
    }),
    {
      name: CONFIG.CONSENT_STORAGE_KEY,
      storage: createJSONStorage(() => AsyncStorage),
    }
  )
);
