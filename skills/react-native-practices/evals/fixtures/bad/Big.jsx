import { FlatList, ScrollView, Text, View, Image } from 'react-native';

export const Big = (props) => (
  <View>
    <ScrollView>
      {Array.from({ length: 200 }).map((_, n) => (
        <Text key={n}>Row {n}</Text>
      ))}
    </ScrollView>
    <FlatList {...props} />
    <FlatList
      data={props.rows}
      keyExtractor={(r) => r.id}
      renderItem={({ item }) => (
        <View style={{ padding: 12, flexDirection: 'row', alignItems: 'center', borderBottomWidth: 1 }}>
          <Image source={{ uri: item.avatar }} style={{ width: 48, height: 48, borderRadius: 24 }} />
          <View style={{ marginLeft: 12, flex: 1 }}>
            <Text style={{ fontWeight: '600', fontSize: 16 }}>{item.name}</Text>
            <Text style={{ color: '#666', marginTop: 2 }}>{item.subtitle}</Text>
            <Text style={{ color: '#999', marginTop: 2 }}>{item.when}</Text>
          </View>
          <Text style={{ fontSize: 12, color: '#999' }}>{item.badge}</Text>
        </View>
      )}
    />
  </View>
);
