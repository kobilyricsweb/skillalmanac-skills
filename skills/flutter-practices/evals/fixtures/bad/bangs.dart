// Strings and comments such as "wow!" or user! must not count.
class Account {
  Account({this.name, this.email, this.phone, this.address});

  final String? name;
  final String? email;
  final String? phone;
  final Map<String, String>? address;

  String describe() {
    final greeting = 'Hello!';
    final a = name!;
    final b = email!.trim();
    final c = phone!.length;
    final d = address!['city']!;
    final e = address!['street']!;
    if (a != b) {
      return greeting + a + b;
    }
    if (!(c > 3)) {
      return d + e;
    }
    return name!.toUpperCase();
  }
}
