import React, { useCallback } from 'react';
import { FlatList, ScrollView, Text, View } from 'react-native';

const Row = React.memo(function Row({ title }: { title: string }) {
  return <Text>{title}</Text>;
});

export function FeedGood({ posts }: { posts: Post[] }) {
  if (__DEV__) console.log('render feed');
  const renderItem = useCallback(({ item }: { item: Post }) => <Row title={item.title} />, []);
  return (
    <View>
      <ScrollView>
        <Text>Short fixed content</Text>
      </ScrollView>
      <FlatList
        data={posts}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
      />
      <FlatList<Post> data={posts} keyExtractor={(p) => p.id} renderItem={renderItem} />
    </View>
  );
}
