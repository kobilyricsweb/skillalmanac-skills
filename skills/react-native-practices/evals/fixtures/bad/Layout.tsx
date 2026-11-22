import { Platform, View } from 'react-native';

export function Layout({ children }) {
  const a = Platform.OS === 'iOS';
  const top = Platform.OS === 'ios' ? 44 : 24;
  const b = Platform.OS === 'android';
  const c = Platform.OS !== 'web';
  return <View style={{ paddingTop: top, opacity: a || b || c ? 1 : 0 }}>{children}</View>;
}
