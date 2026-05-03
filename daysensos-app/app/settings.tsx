/**
 * Settings Screen — Server-URL, Health-Check, Queue
 */

import { useState, useEffect, useCallback } from 'react';
import {
  View, Text, TextInput, Pressable, StyleSheet, ScrollView, Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useDayScoreStore } from '../src/store/dayScore';
import { useCapture } from '../src/store/useCapture';
import { setServerUrl, resetServerUrl } from '../src/network/api';
import { getQueueLength, clearQueue } from '../src/network/queue';
import { CONFIG } from '../src/config';

export default function SettingsScreen() {
  const [url, setUrl] = useState(CONFIG.SERVER_URL);
  const [checking, setChecking] = useState(false);
  const [queueLen, setQueueLen] = useState(0);
  const serverOnline = useDayScoreStore((s) => s.serverOnline);
  const { checkHealth } = useCapture();

  const loadSettings = useCallback(async () => {
    const stored = await AsyncStorage.getItem(CONFIG.SERVER_URL_STORAGE_KEY);
    if (stored) setUrl(stored);
    const len = await getQueueLength();
    setQueueLen(len);
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const handleSave = async () => {
    const trimmed = url.trim().replace(/\/$/, '');
    if (!trimmed.startsWith('http')) {
      Alert.alert('Ungueltige URL', 'URL muss mit http:// oder https:// beginnen.');
      return;
    }
    await setServerUrl(trimmed);
    setUrl(trimmed);
    handleCheck();
  };

  const handleReset = async () => {
    await resetServerUrl();
    setUrl(CONFIG.SERVER_URL);
    handleCheck();
  };

  const handleCheck = async () => {
    setChecking(true);
    await checkHealth();
    setChecking(false);
  };

  const handleClearQueue = async () => {
    Alert.alert('Queue leeren?', `${queueLen} gepufferte Captures werden geloescht.`, [
      { text: 'Abbrechen', style: 'cancel' },
      { text: 'Leeren', style: 'destructive', onPress: async () => { await clearQueue(); setQueueLen(0); } },
    ]);
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Server-Verbindung</Text>
      <Text style={styles.label}>Server-URL</Text>
      <TextInput
        style={styles.input} value={url} onChangeText={setUrl}
        placeholder="http://192.168.5.164:8111" placeholderTextColor="#555"
        autoCapitalize="none" autoCorrect={false} keyboardType="url"
      />
      <Text style={styles.hint}>LAN: http://192.168.x.x:8111 — Tunnel: https://daysensos.example.com</Text>

      <View style={styles.buttonRow}>
        <Pressable style={styles.primaryButton} onPress={handleSave}>
          <Text style={styles.primaryButtonText}>Speichern</Text>
        </Pressable>
        <Pressable style={styles.secondaryButton} onPress={handleReset}>
          <Text style={styles.secondaryButtonText}>Reset</Text>
        </Pressable>
      </View>

      <Pressable style={styles.checkButton} onPress={handleCheck} disabled={checking}>
        <Text style={styles.checkButtonText}>{checking ? 'Pruefe...' : 'Verbindung testen'}</Text>
      </Pressable>

      <View style={styles.statusRow}>
        <View style={[styles.statusDot, { backgroundColor: serverOnline ? '#64ffda' : '#ff5252' }]} />
        <Text style={styles.statusText}>
          {serverOnline ? 'Mac Mini erreichbar (L4-L5 aktiv)' : 'Server nicht erreichbar — Store-and-Forward aktiv'}
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Offline-Queue</Text>
        <View style={styles.infoRow}>
          <Text style={styles.infoLabel}>Gepufferte Captures</Text>
          <Text style={styles.infoValue}>{queueLen}</Text>
        </View>
        {queueLen > 0 && (
          <Pressable style={styles.dangerButton} onPress={handleClearQueue}>
            <Text style={styles.dangerButtonText}>Queue leeren</Text>
          </Pressable>
        )}
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Architektur</Text>
        <Text style={styles.infoText}>
          L1-L3 laufen lokal auf diesem Geraet. L4-L5 laufen auf dem Mac Mini M4.
          Bei fehlender Verbindung werden Captures lokal gepuffert und
          bei naechster Verbindung automatisch synchronisiert.
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f23' },
  content: { padding: 24, paddingBottom: 40 },
  header: { fontSize: 24, fontWeight: '700', color: '#e0e0e0', marginBottom: 24 },
  label: { fontSize: 14, color: '#888', marginBottom: 6 },
  input: { backgroundColor: '#1a1a2e', borderRadius: 10, padding: 14, color: '#e0e0e0', fontSize: 15, borderWidth: 1, borderColor: '#2a2a4e' },
  hint: { fontSize: 12, color: '#555', marginTop: 6, marginBottom: 16 },
  buttonRow: { flexDirection: 'row', gap: 12, marginBottom: 16 },
  primaryButton: { flex: 1, height: 44, backgroundColor: '#64ffda', borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  primaryButtonText: { color: '#1a1a2e', fontWeight: '700', fontSize: 15 },
  secondaryButton: { height: 44, paddingHorizontal: 20, borderWidth: 1, borderColor: '#2a2a4e', borderRadius: 10, justifyContent: 'center', alignItems: 'center' },
  secondaryButtonText: { color: '#888', fontSize: 15 },
  checkButton: { height: 44, borderWidth: 1, borderColor: '#2a2a4e', borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginBottom: 12 },
  checkButtonText: { color: '#aaa', fontSize: 14 },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 32 },
  statusDot: { width: 10, height: 10, borderRadius: 5 },
  statusText: { color: '#888', fontSize: 13, flex: 1 },
  section: { marginBottom: 24 },
  sectionTitle: { fontSize: 18, fontWeight: '600', color: '#e0e0e0', marginBottom: 12 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8 },
  infoLabel: { color: '#888', fontSize: 14 },
  infoValue: { color: '#e0e0e0', fontSize: 14, fontWeight: '600', fontVariant: ['tabular-nums'] },
  infoText: { color: '#888', fontSize: 13, lineHeight: 20 },
  dangerButton: { height: 40, borderWidth: 1, borderColor: '#ff5252', borderRadius: 10, justifyContent: 'center', alignItems: 'center', marginTop: 12 },
  dangerButtonText: { color: '#ff5252', fontSize: 14 },
});
