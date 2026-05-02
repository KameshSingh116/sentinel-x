import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, ScrollView, RefreshControl,
  StyleSheet, TouchableOpacity, ActivityIndicator
} from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { ENDPOINTS, REFRESH_INTERVAL_MS } from '../config';

const C = {
  bg: '#0a0e1a', card: '#0f1629', card2: '#141c35',
  accent: '#00d4ff', accent2: '#7b2ff7', danger: '#ff3860',
  warning: '#ffdd57', success: '#23d160', text: '#ccd6f6',
  muted: '#8892b0', border: 'rgba(0,212,255,0.12)',
};

function StatCard({ label, value, color, icon }) {
  return (
    <View style={[s.statCard, { borderTopColor: color }]}>
      <Ionicons name={icon} size={22} color={color} style={s.statIcon} />
      <Text style={s.statLabel}>{label}</Text>
      <Text style={[s.statValue, { color }]}>{value}</Text>
    </View>
  );
}

function InfoRow({ label, value, valueColor }) {
  return (
    <View style={s.infoRow}>
      <Text style={s.infoLabel}>{label}</Text>
      <Text style={[s.infoValue, valueColor ? { color: valueColor } : {}]}>{value}</Text>
    </View>
  );
}

function ProgressBar({ percent, color }) {
  return (
    <View style={s.progressBg}>
      <View style={[s.progressFill, { width: `${Math.min(percent, 100)}%`, backgroundColor: color }]} />
    </View>
  );
}

export default function DashboardScreen() {
  const [data, setData] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [testMsg, setTestMsg] = useState('');

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [statusRes, alertsRes] = await Promise.all([
        axios.get(ENDPOINTS.status, { timeout: 8000 }),
        axios.get(`${ENDPOINTS.alerts}?limit=1&resolved=false`, { timeout: 8000 }),
      ]);
      setData(statusRes.data.data);
      setStats({ openAlerts: alertsRes.data.count });
    } catch (e) {
      setError('Could not connect to Sentinel-X backend.\nCheck your BASE_URL in config.js.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchData]);

  const onRefresh = () => { setRefreshing(true); fetchData(); };

  const triggerTest = async () => {
    try {
      await axios.post(ENDPOINTS.triggerTest, {}, { timeout: 5000 });
      setTestMsg('Test alert triggered!');
      setTimeout(() => setTestMsg(''), 3000);
    } catch { setTestMsg('Failed to trigger alert'); setTimeout(() => setTestMsg(''), 3000); }
  };

  if (loading) return (
    <View style={s.center}><ActivityIndicator color={C.accent} size="large" /><Text style={s.loadingText}>Connecting to Sentinel-X…</Text></View>
  );

  if (error) return (
    <View style={s.center}>
      <Ionicons name="warning" size={40} color={C.danger} />
      <Text style={s.errorText}>{error}</Text>
      <TouchableOpacity style={s.retryBtn} onPress={fetchData}><Text style={{ color: C.accent, fontWeight: '700' }}>Retry</Text></TouchableOpacity>
    </View>
  );

  const sys = data?.system;
  const net = data?.network;
  const health = sys?.health || 'unknown';
  const healthColor = { healthy: C.success, warning: C.warning, critical: C.danger }[health] || C.muted;

  return (
    <ScrollView style={s.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.accent} />}>
      <View style={s.header}>
        <View style={s.headerLeft}>
          <Ionicons name="shield-checkmark" size={28} color={C.accent} />
          <Text style={s.headerTitle}>System Status</Text>
        </View>
        <View style={[s.healthBadge, { backgroundColor: healthColor + '22', borderColor: healthColor }]}>
          <Text style={[s.healthText, { color: healthColor }]}>{health.toUpperCase()}</Text>
        </View>
      </View>

      <View style={s.statsRow}>
        <StatCard label="CPU" value={`${sys?.cpu?.usage_percent?.toFixed(1)}%`} color={C.accent} icon="hardware-chip-outline" />
        <StatCard label="Memory" value={`${sys?.memory?.usage_percent?.toFixed(1)}%`} color={C.warning} icon="server-outline" />
        <StatCard label="Alerts" value={String(stats?.openAlerts || 0)} color={C.danger} icon="bell-outline" />
        <StatCard label="Connections" value={String(net?.total_connections || 0)} color={C.success} icon="globe-outline" />
      </View>

      <View style={s.card}>
        <Text style={s.cardTitle}><Ionicons name="analytics-outline" size={14} color={C.accent} /> CPU & Memory</Text>
        <InfoRow label="CPU Usage" value={`${sys?.cpu?.usage_percent?.toFixed(1)}%`} valueColor={sys?.cpu?.alert ? C.danger : C.text} />
        <ProgressBar percent={sys?.cpu?.usage_percent || 0} color={C.accent} />
        <View style={{ height: 10 }} />
        <InfoRow label="Memory Usage" value={`${sys?.memory?.usage_percent?.toFixed(1)}%`} valueColor={sys?.memory?.alert ? C.danger : C.text} />
        <ProgressBar percent={sys?.memory?.usage_percent || 0} color={C.warning} />
        <InfoRow label="RAM Total" value={`${sys?.memory?.total_gb} GB`} />
        <InfoRow label="RAM Used" value={`${sys?.memory?.used_gb} GB`} />
        <InfoRow label="CPU Cores" value={String(sys?.cpu?.core_count)} />
        <InfoRow label="Uptime" value={formatUptime(sys?.uptime_seconds || 0)} />
      </View>

      <View style={s.card}>
        <Text style={s.cardTitle}><Ionicons name="wifi-outline" size={14} color={C.accent} /> Network</Text>
        <InfoRow label="Total Connections" value={String(net?.total_connections)} />
        <InfoRow label="Suspicious" value={String(net?.suspicious_connections)} valueColor={net?.suspicious_connections > 0 ? C.danger : C.success} />
        <InfoRow label="Bytes Sent" value={`${net?.io?.bytes_sent_mb} MB`} />
        <InfoRow label="Bytes Received" value={`${net?.io?.bytes_recv_mb} MB`} />
      </View>

      <TouchableOpacity style={s.testBtn} onPress={triggerTest}>
        <Ionicons name="flask-outline" size={16} color="#fff" />
        <Text style={s.testBtnText}>Trigger Test Alert</Text>
      </TouchableOpacity>
      {testMsg ? <Text style={s.testMsg}>{testMsg}</Text> : null}
      <View style={{ height: 20 }} />
    </ScrollView>
  );
}

function formatUptime(secs) {
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  return `${h}h ${m}m`;
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  center: { flex: 1, backgroundColor: C.bg, alignItems: 'center', justifyContent: 'center', padding: 24 },
  loadingText: { color: C.muted, marginTop: 12, fontSize: 14 },
  errorText: { color: C.muted, textAlign: 'center', marginTop: 12, fontSize: 13, lineHeight: 20 },
  retryBtn: { marginTop: 16, padding: 10, borderWidth: 1, borderColor: C.accent, borderRadius: 8, paddingHorizontal: 24 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: 16, paddingBottom: 8 },
  headerLeft: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  headerTitle: { color: C.text, fontSize: 18, fontWeight: '700' },
  healthBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 20, borderWidth: 1 },
  healthText: { fontSize: 11, fontWeight: '700' },
  statsRow: { flexDirection: 'row', flexWrap: 'wrap', paddingHorizontal: 12, gap: 8, marginBottom: 8 },
  statCard: { flex: 1, minWidth: '22%', backgroundColor: C.card, borderRadius: 10, padding: 10, borderTopWidth: 2, alignItems: 'center' },
  statIcon: { marginBottom: 4 },
  statLabel: { color: C.muted, fontSize: 9, textTransform: 'uppercase', letterSpacing: 0.5 },
  statValue: { fontSize: 16, fontWeight: '700', marginTop: 2 },
  card: { backgroundColor: C.card, borderRadius: 12, marginHorizontal: 12, marginBottom: 12, padding: 14, borderWidth: 1, borderColor: C.border },
  cardTitle: { color: C.accent, fontSize: 12, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.8, marginBottom: 12 },
  infoRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 5, borderBottomWidth: 1, borderBottomColor: 'rgba(255,255,255,0.04)' },
  infoLabel: { color: C.muted, fontSize: 13 },
  infoValue: { color: C.text, fontSize: 13, fontWeight: '600' },
  progressBg: { height: 4, backgroundColor: C.bg, borderRadius: 2, overflow: 'hidden' },
  progressFill: { height: 4, borderRadius: 2 },
  testBtn: { backgroundColor: C.accent, marginHorizontal: 12, marginTop: 4, padding: 14, borderRadius: 10, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  testBtnText: { color: '#fff', fontWeight: '700', fontSize: 14 },
  testMsg: { color: C.success, textAlign: 'center', marginTop: 8, fontSize: 13 },
});
