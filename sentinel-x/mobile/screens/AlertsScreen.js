import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, RefreshControl,
  StyleSheet, TouchableOpacity, ActivityIndicator
} from 'react-native';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { ENDPOINTS, REFRESH_INTERVAL_MS } from '../config';

const C = {
  bg: '#0a0e1a', card: '#0f1629', card2: '#141c35',
  accent: '#00d4ff', danger: '#ff3860', warning: '#ffdd57',
  success: '#23d160', text: '#ccd6f6', muted: '#8892b0',
  border: 'rgba(0,212,255,0.12)',
};

const SEV_COLORS = { critical: '#ff3860', high: '#ff9632', medium: '#ffdd57', low: '#23d160', info: '#00d4ff' };
const SEV_ICONS = { critical: 'skull', high: 'warning', medium: 'alert-circle', low: 'information-circle', info: 'information-circle' };

function AlertItem({ item, onResolve }) {
  const color = SEV_COLORS[item.severity] || C.muted;
  return (
    <View style={[s.alertCard, { borderLeftColor: color }]}>
      <View style={s.alertHeader}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
          <Ionicons name={SEV_ICONS[item.severity] || 'alert'} size={16} color={color} />
          <Text style={[s.alertSev, { color }]}>{(item.severity || '').toUpperCase()}</Text>
          <Text style={s.alertType}>{item.alert_type}</Text>
        </View>
        {item.resolved
          ? <View style={s.resolvedBadge}><Text style={s.resolvedText}>RESOLVED</Text></View>
          : <TouchableOpacity style={s.resolveBtn} onPress={() => onResolve(item.id)}>
              <Text style={s.resolveBtnText}>Resolve</Text>
            </TouchableOpacity>
        }
      </View>
      <Text style={s.alertMsg}>{item.message}</Text>
      <Text style={s.alertTime}><Ionicons name="time-outline" size={11} /> {new Date(item.timestamp).toLocaleString()}</Text>
    </View>
  );
}

export default function AlertsScreen() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('open');

  const fetchAlerts = useCallback(async () => {
    try {
      setError(null);
      const resolved = filter === 'open' ? 'false' : filter === 'resolved' ? 'true' : '';
      const url = `${ENDPOINTS.alerts}?limit=100${resolved !== '' ? `&resolved=${resolved}` : ''}`;
      const res = await axios.get(url, { timeout: 8000 });
      setAlerts(res.data.data || []);
    } catch (e) {
      setError('Could not load alerts. Check backend connection.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [filter]);

  useEffect(() => { fetchAlerts(); }, [fetchAlerts]);
  useEffect(() => {
    const interval = setInterval(fetchAlerts, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const resolveAlert = async (id) => {
    try {
      await axios.post(`${ENDPOINTS.alerts}/${id}/resolve`, {}, { timeout: 5000 });
      fetchAlerts();
    } catch {}
  };

  const filterBtns = ['all', 'open', 'resolved'];

  return (
    <View style={s.container}>
      <View style={s.filterRow}>
        {filterBtns.map(f => (
          <TouchableOpacity key={f} style={[s.filterBtn, filter === f && s.filterBtnActive]} onPress={() => setFilter(f)}>
            <Text style={[s.filterBtnText, filter === f && { color: C.accent }]}>{f.toUpperCase()}</Text>
          </TouchableOpacity>
        ))}
        <Text style={s.countText}>{alerts.length} alerts</Text>
      </View>

      {loading ? (
        <View style={s.center}><ActivityIndicator color={C.accent} /></View>
      ) : error ? (
        <View style={s.center}>
          <Ionicons name="warning" size={32} color={C.danger} />
          <Text style={s.errorText}>{error}</Text>
          <TouchableOpacity onPress={fetchAlerts} style={s.retryBtn}><Text style={{ color: C.accent }}>Retry</Text></TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={alerts}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => <AlertItem item={item} onResolve={resolveAlert} />}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchAlerts(); }} tintColor={C.accent} />}
          ListEmptyComponent={<View style={s.center}><Ionicons name="checkmark-circle" size={40} color={C.success} /><Text style={s.emptyText}>No alerts found</Text></View>}
          contentContainerStyle={{ padding: 12, paddingBottom: 20, flexGrow: 1 }}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  filterRow: { flexDirection: 'row', padding: 12, gap: 8, alignItems: 'center', borderBottomWidth: 1, borderBottomColor: C.border },
  filterBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: C.border },
  filterBtnActive: { borderColor: C.accent, backgroundColor: 'rgba(0,212,255,0.1)' },
  filterBtnText: { color: C.muted, fontSize: 11, fontWeight: '700' },
  countText: { marginLeft: 'auto', color: C.muted, fontSize: 12 },
  alertCard: { backgroundColor: C.card, borderRadius: 10, padding: 12, marginBottom: 10, borderLeftWidth: 3, borderWidth: 1, borderColor: C.border },
  alertHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  alertSev: { fontSize: 11, fontWeight: '700' },
  alertType: { color: C.muted, fontSize: 12 },
  alertMsg: { color: C.text, fontSize: 13, lineHeight: 18, marginBottom: 6 },
  alertTime: { color: C.muted, fontSize: 11 },
  resolvedBadge: { backgroundColor: 'rgba(35,209,96,0.1)', paddingHorizontal: 8, paddingVertical: 3, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(35,209,96,0.3)' },
  resolvedText: { color: C.success, fontSize: 10, fontWeight: '700' },
  resolveBtn: { borderWidth: 1, borderColor: C.accent, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  resolveBtnText: { color: C.accent, fontSize: 11, fontWeight: '600' },
  errorText: { color: C.muted, textAlign: 'center', marginTop: 10, fontSize: 13 },
  retryBtn: { marginTop: 12, padding: 8, borderWidth: 1, borderColor: C.accent, borderRadius: 8, paddingHorizontal: 20 },
  emptyText: { color: C.muted, marginTop: 12, fontSize: 14 },
});
