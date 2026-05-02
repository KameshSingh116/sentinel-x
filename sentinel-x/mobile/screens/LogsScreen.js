import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, FlatList, RefreshControl,
  StyleSheet, TouchableOpacity, ActivityIndicator, TextInput
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

const SEV_COLORS = { critical: '#ff3860', high: '#ff9632', warning: '#ffdd57', medium: '#ffdd57', info: '#00d4ff', error: '#ff3860', low: '#23d160' };

function LogItem({ item }) {
  const color = SEV_COLORS[item.severity] || C.muted;
  return (
    <View style={[s.logCard, { borderLeftColor: color }]}>
      <View style={s.logHeader}>
        <View style={[s.sevBadge, { backgroundColor: color + '22', borderColor: color + '55' }]}>
          <Text style={[s.sevText, { color }]}>{(item.severity || '').toUpperCase()}</Text>
        </View>
        <Text style={s.eventType}>{item.event_type}</Text>
        <Text style={s.sourceText}>{item.source}</Text>
      </View>
      <Text style={s.descText}>{item.description}</Text>
      <Text style={s.timeText}><Ionicons name="time-outline" size={11} /> {new Date(item.timestamp).toLocaleString()}</Text>
    </View>
  );
}

export default function LogsScreen() {
  const [logs, setLogs] = useState([]);
  const [allLogs, setAllLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [sevFilter, setSevFilter] = useState('');
  const [stats, setStats] = useState(null);

  const fetchLogs = useCallback(async () => {
    try {
      setError(null);
      let url = `${ENDPOINTS.logs}?limit=200`;
      if (sevFilter) url += `&severity=${sevFilter}`;
      const res = await axios.get(url, { timeout: 8000 });
      setAllLogs(res.data.data || []);
      setStats(res.data.stats);
    } catch (e) {
      setError('Could not load logs. Check backend connection.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [sevFilter]);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);
  useEffect(() => {
    const interval = setInterval(fetchLogs, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  useEffect(() => {
    const q = search.toLowerCase();
    setLogs(q ? allLogs.filter(l =>
      (l.event_type || '').toLowerCase().includes(q) ||
      (l.description || '').toLowerCase().includes(q) ||
      (l.source || '').toLowerCase().includes(q)
    ) : allLogs);
  }, [search, allLogs]);

  const sevOptions = ['', 'critical', 'high', 'warning', 'info', 'error'];

  return (
    <View style={s.container}>
      {stats && (
        <View style={s.statsBar}>
          <Text style={s.statsText}>Events: <Text style={{ color: C.accent }}>{stats.total_events}</Text></Text>
          <Text style={s.statsText}>Alerts: <Text style={{ color: C.danger }}>{stats.total_alerts}</Text></Text>
          <Text style={s.statsText}>Open: <Text style={{ color: C.warning }}>{stats.open_alerts}</Text></Text>
        </View>
      )}

      <View style={s.controls}>
        <TextInput
          style={s.searchInput}
          placeholder="Search logs…"
          placeholderTextColor={C.muted}
          value={search}
          onChangeText={setSearch}
        />
      </View>

      <View style={s.sevRow}>
        {sevOptions.map(sev => (
          <TouchableOpacity
            key={sev || 'all'}
            style={[s.sevBtn, sevFilter === sev && s.sevBtnActive]}
            onPress={() => setSevFilter(sev)}
          >
            <Text style={[s.sevBtnText, { color: sev ? (SEV_COLORS[sev] || C.muted) : C.accent }, sevFilter !== sev && { opacity: 0.5 }]}>
              {sev ? sev.toUpperCase() : 'ALL'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading ? (
        <View style={s.center}><ActivityIndicator color={C.accent} /></View>
      ) : error ? (
        <View style={s.center}>
          <Ionicons name="warning" size={32} color={C.danger} />
          <Text style={s.errorText}>{error}</Text>
          <TouchableOpacity onPress={fetchLogs} style={s.retryBtn}><Text style={{ color: C.accent }}>Retry</Text></TouchableOpacity>
        </View>
      ) : (
        <FlatList
          data={logs}
          keyExtractor={item => String(item.id)}
          renderItem={({ item }) => <LogItem item={item} />}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); fetchLogs(); }} tintColor={C.accent} />}
          ListEmptyComponent={<View style={s.center}><Ionicons name="document-outline" size={40} color={C.muted} /><Text style={s.emptyText}>No logs found</Text></View>}
          contentContainerStyle={{ padding: 12, paddingBottom: 20, flexGrow: 1 }}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: 24 },
  statsBar: { flexDirection: 'row', gap: 16, padding: 10, paddingHorizontal: 14, backgroundColor: C.card, borderBottomWidth: 1, borderBottomColor: C.border },
  statsText: { color: C.muted, fontSize: 12 },
  controls: { padding: 10 },
  searchInput: { backgroundColor: C.card, color: C.text, borderRadius: 8, padding: 10, fontSize: 13, borderWidth: 1, borderColor: C.border },
  sevRow: { flexDirection: 'row', paddingHorizontal: 10, gap: 6, marginBottom: 8, flexWrap: 'wrap' },
  sevBtn: { paddingHorizontal: 10, paddingVertical: 5, borderRadius: 16, borderWidth: 1, borderColor: C.border },
  sevBtnActive: { backgroundColor: 'rgba(0,212,255,0.08)', borderColor: C.accent },
  sevBtnText: { fontSize: 10, fontWeight: '700' },
  logCard: { backgroundColor: C.card, borderRadius: 8, padding: 10, marginBottom: 8, borderLeftWidth: 3, borderWidth: 1, borderColor: C.border },
  logHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 5 },
  sevBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 10, borderWidth: 1 },
  sevText: { fontSize: 9, fontWeight: '700' },
  eventType: { color: C.accent, fontSize: 12, fontWeight: '600', flex: 1 },
  sourceText: { color: C.muted, fontSize: 10 },
  descText: { color: C.text, fontSize: 12, lineHeight: 17, marginBottom: 5 },
  timeText: { color: C.muted, fontSize: 10 },
  errorText: { color: C.muted, textAlign: 'center', marginTop: 10, fontSize: 13 },
  retryBtn: { marginTop: 12, padding: 8, borderWidth: 1, borderColor: C.accent, borderRadius: 8, paddingHorizontal: 20 },
  emptyText: { color: C.muted, marginTop: 12, fontSize: 14 },
});
