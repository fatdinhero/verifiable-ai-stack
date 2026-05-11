"""DaySensOS — Pytest Suite (L1-L5)."""
import pytest
from datetime import datetime
from daysensos.models import (
    SensorData, ConsentState, ContextID, SituationResult,
    Episode, DayFeatures, WellnessState,
)
from daysensos.consent import apply_consent_gate
from daysensos.l1_perception import process_l1, compute_movement_magnitude
from daysensos.l2_situation import classify_context
from daysensos.l3_episodes import EpisodeTracker
from daysensos.l4_features import compute_day_features
from daysensos.l5_intelligence import compute_day_score


class TestConsentGate:
    def test_camera_default_off(self):
        data = SensorData(camera_context="office")
        assert apply_consent_gate(data).camera_context is None

    def test_microphone_default_off(self):
        data = SensorData(freq_spectrum=[0.1, 0.2])
        assert apply_consent_gate(data).freq_spectrum is None

    def test_gps_default_on(self):
        data = SensorData(gps_lat=48.89, gps_lon=8.69)
        assert apply_consent_gate(data).gps_lat == 48.89

    def test_camera_on_with_consent(self):
        data = SensorData(camera_context="park", consent_state=ConsentState(camera=True))
        assert apply_consent_gate(data).camera_context == "park"

    def test_gps_off_without_consent(self):
        data = SensorData(gps_lat=48.89, consent_state=ConsentState(gps=False))
        assert apply_consent_gate(data).gps_lat is None

    def test_bt_cleared_without_consent(self):
        data = SensorData(bt_devices=["a","b"], consent_state=ConsentState(bt_scan=False))
        assert apply_consent_gate(data).bt_devices == []

    def test_all_defaults_safe(self):
        c = ConsentState()
        assert c.camera is False
        assert c.microphone is False
        assert c.gps is True


class TestL1Perception:
    def test_movement_still(self):
        data = SensorData(accel_x=0.0, accel_y=0.0, accel_z=9.81)
        assert compute_movement_magnitude(data) == pytest.approx(0.0, abs=0.05)

    def test_movement_active(self):
        data = SensorData(accel_x=5.0, accel_y=5.0, accel_z=9.81)
        assert compute_movement_magnitude(data) > 2.0

    def test_movement_no_accel(self):
        assert compute_movement_magnitude(SensorData()) == 0.0

    def test_process_l1_keys(self):
        signals = process_l1(SensorData(gps_lat=48.89, light_lux=500))
        for k in ["gps_lat","movement_magnitude","bt_device_count","ambient_noise_db"]:
            assert k in signals

    def test_zero_retention_camera(self):
        signals = process_l1(SensorData(camera_context="office"))
        assert signals["camera_context"] is None


class TestL2Situation:
    def test_sleep(self):
        r = classify_context({"timestamp": datetime.utcnow().isoformat(), "movement_magnitude": 0.1, "light_lux": 5, "screen_time_min": 0})
        assert r.context_id == ContextID.SLEEP

    def test_exercise(self):
        r = classify_context({"timestamp": datetime.utcnow().isoformat(), "movement_magnitude": 4.0})
        assert r.context_id == ContextID.EXERCISE

    def test_deep_work(self):
        r = classify_context({"timestamp": datetime.utcnow().isoformat(), "screen_time_min": 45, "movement_magnitude": 0.2, "bt_device_count": 1})
        assert r.context_id == ContextID.DEEP_WORK

    def test_fallback(self):
        r = classify_context({"timestamp": datetime.utcnow().isoformat()})
        assert r.context_id in list(ContextID)

    def test_confidence_range(self):
        r = classify_context({"timestamp": datetime.utcnow().isoformat(), "movement_magnitude": 0.1, "light_lux": 5, "screen_time_min": 0})
        assert 0.0 < r.confidence <= 1.0


class TestL3Episodes:
    def test_starts_episode(self):
        t = EpisodeTracker()
        ep = t.process(SituationResult(context_id=ContextID.DEEP_WORK, confidence=0.8, timestamp=datetime.utcnow()))
        assert ep.context_id == ContextID.DEEP_WORK

    def test_continues_same(self):
        t = EpisodeTracker()
        s = SituationResult(context_id=ContextID.DEEP_WORK, confidence=0.8, timestamp=datetime.utcnow())
        assert t.process(s).context_id == t.process(s).context_id

    def test_buffer_prevents_flicker(self):
        t = EpisodeTracker()
        for _ in range(3):
            t.process(SituationResult(context_id=ContextID.DEEP_WORK, confidence=0.8, timestamp=datetime.utcnow()))
        t.process(SituationResult(context_id=ContextID.REST, confidence=0.6, timestamp=datetime.utcnow()))
        assert t.current_episode.context_id == ContextID.DEEP_WORK

    def test_buffer_allows_real_switch(self):
        t = EpisodeTracker()
        for _ in range(3):
            t.process(SituationResult(context_id=ContextID.DEEP_WORK, confidence=0.8, timestamp=datetime.utcnow()))
        for _ in range(3):
            t.process(SituationResult(context_id=ContextID.REST, confidence=0.7, timestamp=datetime.utcnow()))
        assert t.current_episode.context_id == ContextID.REST


class TestL4Features:
    def test_features_range(self):
        eps = [
            Episode(context_id=ContextID.DEEP_WORK, start_time=datetime.utcnow(), duration_min=120),
            Episode(context_id=ContextID.EXERCISE, start_time=datetime.utcnow(), duration_min=45),
        ]
        f = compute_day_features(eps)
        for dim in [f.focus, f.energy, f.social, f.movement]:
            assert 0.0 <= dim <= 10.0

    def test_empty_episodes(self):
        f = compute_day_features([])
        assert 0.0 <= f.focus <= 5.0  # Depends on 14-day history
        assert f.episodes_count == 0

    def test_no_biometric_leak(self):
        f = compute_day_features([])
        for attr in ["heart_rate","blood_pressure","sleep_stages"]:
            assert not hasattr(f, attr)

    def test_total_tracked(self):
        eps = [
            Episode(context_id=ContextID.DEEP_WORK, start_time=datetime.utcnow(), duration_min=60),
            Episode(context_id=ContextID.REST, start_time=datetime.utcnow(), duration_min=30),
        ]
        assert compute_day_features(eps).total_tracked_min == 90.0


class TestL5Intelligence:
    def test_score_range(self):
        f = DayFeatures(date="2026-05-03", focus=7.0, energy=6.0, social=5.0, movement=4.0)
        assert 0.0 <= compute_day_score(f).score <= 10.0

    def test_no_gamification(self):
        f = DayFeatures(date="2026-05-03", focus=9.0, energy=8.0, social=7.0, movement=6.0)
        ds = compute_day_score(f)
        for attr in ["streak","rank","highscore"]:
            assert not hasattr(ds, attr)

    def test_thriving(self):
        f = DayFeatures(date="2026-05-03", focus=10.0, energy=8.0, social=6.0, movement=5.0)
        assert compute_day_score(f).wellness == WellnessState.THRIVING

    def test_balanced(self):
        f = DayFeatures(date="2026-05-03", focus=7.0, energy=6.0, social=5.0, movement=5.0)
        assert compute_day_score(f).wellness == WellnessState.BALANCED

    def test_recommendations_exist(self):
        f = DayFeatures(date="2026-05-03", focus=2.0, energy=2.0, social=1.0, movement=1.0)
        assert len(compute_day_score(f).recommendations) > 0

    def test_no_medical_claims(self):
        f = DayFeatures(date="2026-05-03", focus=2.0, energy=2.0, social=1.0, movement=1.0)
        for rec in compute_day_score(f).recommendations:
            for word in ["diagnos","krankheit","therapie"]:
                assert word not in rec.lower()
