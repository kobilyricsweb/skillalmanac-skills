import React from 'react';
import { ScrollView, FlatList, Text, View } from 'react-native';

export function Feed({ posts, tabs }: { posts: Post[]; tabs: string[] }) {
  console.log('render feed', posts.length);
  return (
    <View>
      <ScrollView horizontal>
        {tabs.map((t) => (
          <Text key={t}>{t}</Text>
        ))}
      </ScrollView>
      <ScrollView>
        {posts.map((p) => (
          <Text key={p.id}>{p.title}</Text>
        ))}
      </ScrollView>
      <FlatList
        data={posts}
        renderItem={({ item }) => <Text>{item.title}</Text>}
      />
      <FlatList
        data={posts}
        keyExtractor={(_, index) => String(index)}
        renderItem={renderRow}
      />
    </View>
  );
}
// console.log('commented out, must not be reported');
