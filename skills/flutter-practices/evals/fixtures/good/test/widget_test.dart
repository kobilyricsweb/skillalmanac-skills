import 'package:flutter_test/flutter_test.dart';

void main() {
  test('exempt from print and bang rules', () {
    final value = int.tryParse('4');
    print('value is $value');
    final a = value!;
    final b = value!;
    final c = value!;
    final d = value!;
    final e = value!;
    final f = value!;
    final g = value!;
    final h = value!;
    expect(a + b + c + d + e + f + g + h, 32);
  });
}
