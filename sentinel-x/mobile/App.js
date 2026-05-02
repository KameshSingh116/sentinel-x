import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { StatusBar } from 'expo-status-bar';

import DashboardScreen from './screens/DashboardScreen';
import AlertsScreen from './screens/AlertsScreen';
import LogsScreen from './screens/LogsScreen';

const Tab = createBottomTabNavigator();

const COLORS = {
  bg: '#0a0e1a',
  card: '#0f1629',
  accent: '#00d4ff',
  inactive: '#4a5568',
  danger: '#ff3860',
  text: '#ccd6f6',
};

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerStyle: { backgroundColor: COLORS.card, borderBottomColor: 'rgba(0,212,255,0.12)', borderBottomWidth: 1 },
          headerTintColor: COLORS.text,
          headerTitleStyle: { fontWeight: '700', fontSize: 16 },
          tabBarStyle: { backgroundColor: COLORS.card, borderTopColor: 'rgba(0,212,255,0.12)', height: 60, paddingBottom: 8 },
          tabBarActiveTintColor: COLORS.accent,
          tabBarInactiveTintColor: COLORS.inactive,
          tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
          tabBarIcon: ({ focused, color, size }) => {
            const icons = {
              Dashboard: focused ? 'speedometer' : 'speedometer-outline',
              Alerts: focused ? 'warning' : 'warning-outline',
              Logs: focused ? 'list' : 'list-outline',
            };
            return <Ionicons name={icons[route.name]} size={size} color={color} />;
          },
        })}
      >
        <Tab.Screen name="Dashboard" component={DashboardScreen} options={{ title: 'Sentinel-X' }} />
        <Tab.Screen name="Alerts" component={AlertsScreen} />
        <Tab.Screen name="Logs" component={LogsScreen} />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
