import React from 'react';
import { View, Text, Pressable, FlatList, Platform } from 'react-native';

export function ProfileScreen({ friends, onRemove }) {
  console.debug('profile render');
  const pad = Platform.OS === 'android' ? 24 : 0;
  return (
    <View style={{ paddingTop: pad }}>
      <FlatList
        data={friends}
        keyExtractor={(f) => f.id}
        renderItem={({ item }) => (
          <Pressable onPress={() => onRemove(item.id)}>
            <Text>{item.name}</Text>
          </Pressable>
        )}
      />
    </View>
  );
}
