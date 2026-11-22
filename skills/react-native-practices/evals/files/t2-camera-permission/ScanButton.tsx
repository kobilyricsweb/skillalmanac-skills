import React from 'react';
import { Pressable, Text, Platform } from 'react-native';
import { Camera } from 'expo-camera';

export function ScanButton({ onScan }: { onScan: () => void }) {
  async function start() {
    const { status } = await Camera.requestCameraPermissionsAsync();
    if (status === 'granted') {
      onScan();
    }
  }
  return (
    <Pressable onPress={start} style={{ marginTop: Platform.OS === 'iOS' ? 44 : 0 }}>
      <Text>Scan</Text>
    </Pressable>
  );
}
