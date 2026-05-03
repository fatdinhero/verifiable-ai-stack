/**
 * Dashboard Screen — DayScore + Episode + Capture Button
 */

import { useState, useEffect } from 'react';
import {
  View, Text, Pressable, StyleSheet, ActivityIndicator,
} from 'react-native';
import { useDayScoreStore } from '../src/store/dayScore';
import { useCapture } from '../src/store/useCapture';

export default function DashboardScreen() {
  const [autoCapture, setAutoCapture] = useState(false);
  const [capturing, setCapturing] = useState(false);

  const focusScore = useDayScoreStore((s) => s.focusScore);
  const episode = useDayScoreStore((s) => s.episode);
  const nudge = useDayScoreStore((s) => s.nudge);
  const lastUpdated = useDayScoreStore((s) => s.lastUpdated);
  const serverOnline = useDayScoreStore((s) => s.serverOnline);
  const queueLength = useDayScoreStore((s) => s.queueLength);

  const { capture, checkHealth } = useCapture({ autoCapture, intervalMs: 60_000 });

  useEffect(() => { checkHealth(); }, [checkHealth]);

  const handleCapture = async () => {
    setCapturing(true);
    await capture();
    setCapturing(false);
  };

  const scoreColor = focusScore !== null
    ? focusScore >= 7 ? '#64ffda' : focusScore >= 4 ? '#ffd740' : '#ff5252'
    : '#666';

  const formatTime = (iso: string | null) => {
    if (!iso) return '\u2014';
    return new Date(iso).toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
  };

  const episodeLabels: Record<string, string> = {
    deep_work: 'Deep Work', commute: 'Unterwegs', social: 'Sozial',
    rest: 'Ruhe', exercise: 'Bewegung', unknown: 'Unbekannt',
  };

  return (
    <View style={styles.container}>
      <View style={styles.scoreContainer}>
        <View style={[styles.scoreCircle, { borderColor: scoreColor }]}>
          <Text style={[styles.scoreValue, { color: scoreColor }]}>
            {focusScore !== null ? focusScore.toFixed(1) : '\u2014'}
          </Text>
          <Text style={styles.scoreLabel}>DayScore</Text>
        </View>
      </View>

      <View style={styles.infoRow}>
        <Text style={styles.infoLabel}>Episode</Text>
        <Text style={styles.infoValue}>
          {episode ? (episodeLabels[episode] ?? episode) : '\u2014'}
        </Text>
      </View>

      {nudge && (
        <View style={styles.nudgeBox}>
          <Text style={styles.nudgeText}>{nudge}</Text>
        </View>
      )}

      <View style={styles.statusBar}>
        <View style={styles.statusItem}>
          <View style={[styles.statusDot, { backgroundColor: serverOnline ? '#64ffda' : '#ff5252' }]} />
          <Text style={styles.statusText}>
            {serverOnline ? 'Server verbunden' : 'Offline'}
          </Text>
        </View>
        {queueLength > 0 && (
          <Text style={styles.queueText}>{queueLength} gepuffert</Text>
        )}
        <Text style={styles.timeText}>{formatTime(lastUpdated)}</Text>
      </View>

      <Pressable
        style={[styles.captureButton, capturing && styles.captureButtonActive]}
        onPress={handleCapture}
        disabled={capturing}
      >
        {capturing ? (
          <ActivityIndicator color="#1a1a2e" />
        ) : (
          <Text style={styles.captureButtonText}>Erfassen</Text>
        )}
      </Pressable>

      <Pressable
        style={[styles.autoButton, autoCapture && styles.autoButtonActive]}
        onPress={() => setAutoCapture(!autoCapture)}
      >
        <Text style={styles.autoButtonText}>
          Auto-Erfassung {autoCapture ? 'AN' : 'AUS'}
        </Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f23', alignItems: 'center', paddingTop: 40, paddingHorizontal: 24 },
  scoreContainer: { marginBottom: 32 },
  scoreCircle: { width: 180, height: 180, borderRadius: 90, borderWidth: 4, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1a2e' },
  scoreValue: { fontSize: 48, fontWeight: '700', fontVariant: ['tabular-nums'] },
  scoreLabel: { fontSize: 14, color: '#888', marginTop: 4 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', width: '100%', paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#2a2a4e' },
  infoLabel: { fontSize: 16, color: '#888' },
  infoValue: { fontSize: 16, color: '#e0e0e0', fontWeight: '600' },
  nudgeBox: { width: '100%', backgroundColor: '#1a1a2e', borderRadius: 12, padding: 16, marginTop: 16, borderLeftWidth: 3, borderLeftColor: '#64ffda' },
  nudgeText: { color: '#e0e0e0', fontSize: 14, lineHeight: 20 },
  statusBar: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', width: '100%', marginTop: 24, paddingVertical: 8 },
  statusItem: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  statusText: { color: '#888', fontSize: 13 },
  queueText: { color: '#ffd740', fontSize: 13 },
  timeText: { color: '#666', fontSize: 13, fontVariant: ['tabular-nums'] },
  captureButton: { width: '100%', height: 52, backgroundColor: '#64ffda', borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginTop: 32 },
  captureButtonActive: { opacity: 0.6 },
  captureButtonText: { color: '#1a1a2e', fontSize: 18, fontWeight: '700' },
  autoButton: { width: '100%', height: 44, borderWidth: 1, borderColor: '#2a2a4e', borderRadius: 12, justifyContent: 'center', alignItems: 'center', marginTop: 12 },
  autoButtonActive: { borderColor: '#64ffda', backgroundColor: 'rgba(100, 255, 218, 0.1)' },
  autoButtonText: { color: '#888', fontSize: 14 },
});
