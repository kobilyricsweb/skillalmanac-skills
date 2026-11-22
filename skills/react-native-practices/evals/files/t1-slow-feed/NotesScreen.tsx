import React, { useEffect, useState } from 'react';
import { ScrollView, View, Text, Image, Pressable } from 'react-native';

type Note = { id: string; title: string; body: string; cover: string };

export default function NotesScreen({ navigation }: any) {
  const [notes, setNotes] = useState<Note[]>([]);
  useEffect(() => {
    fetch('https://api.example.test/notes?limit=2000')
      .then((r) => r.json())
      .then(setNotes);
  }, []);
  console.log('notes loaded', notes.length);
  return (
    <ScrollView>
      {notes.map((note, index) => (
        <Pressable key={index} onPress={() => navigation.navigate('Note', { note })}>
          <Image source={{ uri: note.cover }} />
          <Text>{note.title}</Text>
        </Pressable>
      ))}
    </ScrollView>
  );
}
