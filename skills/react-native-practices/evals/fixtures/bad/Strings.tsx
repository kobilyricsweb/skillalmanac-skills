import { Platform, Text, View } from 'react-native';

const HELP = "Platform.OS === 'Android' and console.log(x)";
const NOTE = 'call console.log(value) only inside __DEV__';

export function Strings() {
  // console.log('this comment is ignored');
  const label = `use Platform.OS === 'IOS' sparingly`;
  const pad = Platform.OS === 'ios'
    ? 20
    : 8;
  console.log(HELP, NOTE, label);
  return (
    <View style={{ paddingTop: pad }}>
      <Text>Don't panic</Text>
    </View>
  );
}
