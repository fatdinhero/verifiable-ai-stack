/**
 * Consent Screen — Per-Sensor Consent Gate (Art. 2, Erkenntnis 10)
 */

import { View, Text, Switch, StyleSheet, ScrollView } from 'react-native';
import { useConsentStore } from '../src/consent/store';
import { SensorChannel } from '../src/sensors/types';

interface SensorInfo {
  channel: SensorChannel;
  label: string;
  description: string;
  privacy: string;
  canDisable: boolean;
}

const SENSORS: SensorInfo[] = [
  { channel: 'gps', label: 'GPS + Standort', description: 'Primaersensor fuer Kontexterkennung.', privacy: 'Koordinaten bleiben lokal.', canDisable: true },
  { channel: 'accelerometer', label: 'Beschleunigung + Gyro', description: 'Erkennt Bewegung, Gehen, Sitzen.', privacy: 'Nur aggregierter Bewegungsvektor.', canDisable: true },
  { channel: 'light', label: 'Lichtsensor', description: 'Umgebungshelligkeit.', privacy: 'Nur Lux-Wert, keine Bilddaten.', canDisable: true },
  { channel: 'bt_scan', label: 'Bluetooth-Scan', description: 'Erkennt Geraete in der Naehe.', privacy: 'MAC-Adressen werden gehasht (SHA-256).', canDisable: true },
  { channel: 'screen_time', label: 'Bildschirmzeit', description: 'App-Nutzungsdauer.', privacy: 'Nur Gesamtdauer, keine App-Namen.', canDisable: true },
  { channel: 'clock', label: 'System-Uhr', description: 'Timestamps fuer Segmentierung.', privacy: 'Reine Zeitstempel, immer aktiv.', canDisable: false },
  { channel: 'camera', label: 'Kamera (Opt-In)', description: 'Visuelle Kontexterkennung. Default AUS.', privacy: 'PixelGuard: KEIN Bild auf Disk. Zero-Retention.', canDisable: true },
  { channel: 'microphone', label: 'Mikrofon (Opt-In)', description: 'Frequenzspektrum. Default AUS.', privacy: 'KEIN Rohaudio. Nur Spektrum.', canDisable: true },
];

export default function ConsentScreen() {
  const consent = useConsentStore((s) => s.consent);
  const setConsent = useConsentStore((s) => s.setConsent);
  const activeCount = Object.values(consent).filter(Boolean).length;

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.header}>Sensorkanaele</Text>
      <Text style={styles.subheader}>{activeCount} von 8 aktiv</Text>

      <View style={styles.privacyBanner}>
        <Text style={styles.privacyBannerText}>
          Alle Daten bleiben auf deinem Geraet (Art. 1: Zero-Retention).
          Kamera und Mikrofon sind standardmaessig AUS.
        </Text>
      </View>

      {SENSORS.map((sensor) => (
        <View key={sensor.channel} style={styles.sensorCard}>
          <View style={styles.sensorHeader}>
            <View style={styles.sensorLabelRow}>
              <View style={[styles.statusDot, { backgroundColor: consent[sensor.channel] ? '#64ffda' : '#444' }]} />
              <Text style={styles.sensorLabel}>{sensor.label}</Text>
            </View>
            <Switch
              value={consent[sensor.channel]}
              onValueChange={(val) => setConsent(sensor.channel, val)}
              disabled={!sensor.canDisable}
              trackColor={{ false: '#333', true: 'rgba(100, 255, 218, 0.3)' }}
              thumbColor={consent[sensor.channel] ? '#64ffda' : '#666'}
            />
          </View>
          <Text style={styles.sensorDescription}>{sensor.description}</Text>
          <Text style={styles.sensorPrivacy}>{sensor.privacy}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0f0f23' },
  content: { padding: 24, paddingBottom: 40 },
  header: { fontSize: 24, fontWeight: '700', color: '#e0e0e0' },
  subheader: { fontSize: 14, color: '#888', marginTop: 4, marginBottom: 16 },
  privacyBanner: { backgroundColor: 'rgba(100, 255, 218, 0.08)', borderRadius: 12, padding: 14, marginBottom: 20, borderWidth: 1, borderColor: 'rgba(100, 255, 218, 0.15)' },
  privacyBannerText: { color: '#64ffda', fontSize: 13, lineHeight: 18 },
  sensorCard: { backgroundColor: '#1a1a2e', borderRadius: 12, padding: 16, marginBottom: 12 },
  sensorHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  sensorLabelRow: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  statusDot: { width: 8, height: 8, borderRadius: 4 },
  sensorLabel: { fontSize: 16, fontWeight: '600', color: '#e0e0e0' },
  sensorDescription: { fontSize: 13, color: '#aaa', lineHeight: 18 },
  sensorPrivacy: { fontSize: 12, color: '#64ffda', marginTop: 6, fontStyle: 'italic' },
});
