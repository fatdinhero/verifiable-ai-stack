/**
 * DayScore Store — hält aktuellen Score + Episode vom Server
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { CaptureResponse } from '../sensors/types';
import { CONFIG } from '../config';

interface DayScoreState {
  focusScore: number | null;
  episode: string | null;
  nudge: string | null;
  lastUpdated: string | null;
  serverOnline: boolean;
  queueLength: number;
  updateFromCapture: (response: CaptureResponse) => void;
  setServerOnline: (online: boolean) => void;
  setQueueLength: (length: number) => void;
}

export const useDayScoreStore = create<DayScoreState>()(
  persist(
    (set) => ({
      focusScore: null,
      episode: null,
      nudge: null,
      lastUpdated: null,
      serverOnline: false,
      queueLength: 0,
      updateFromCapture: (response: CaptureResponse) =>
        set({
          focusScore: response.focus_score,
          episode: response.episode,
          nudge: response.nudge,
          lastUpdated: new Date().toISOString(),
        }),
      setServerOnline: (online: boolean) => set({ serverOnline: online }),
      setQueueLength: (length: number) => set({ queueLength: length }),
    }),
    {
      name: CONFIG.DAYSCORE_STORAGE_KEY,
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        focusScore: state.focusScore,
        episode: state.episode,
        nudge: state.nudge,
        lastUpdated: state.lastUpdated,
      }),
    }
  )
);
