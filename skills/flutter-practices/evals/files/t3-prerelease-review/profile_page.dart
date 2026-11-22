import 'package:flutter/material.dart';

class ProfilePage extends StatelessWidget {
  const ProfilePage({super.key, required this.user});

  final Map<String, dynamic>? user;

  @override
  Widget build(BuildContext context) {
    print('rendering profile for ${user!['id']}');
    final name = user!['name'] as String;
    final email = user!['email'] as String;
    final phone = user!['phone'] as String;
    final city = user!['address']!['city'] as String;
    return Scaffold(
      backgroundColor: Color(0xFFFFFFFF),
      appBar: AppBar(title: Text('Profile')),
      body: Column(
        children: [
          GestureDetector(
            onTap: () => Navigator.of(context).pop(),
            child: Icon(Icons.close, size: 16),
          ),
          Text(name, style: TextStyle(fontSize: 14, color: Color(0xFF999999))),
          Text(email),
          Text(phone),
          Text(city),
        ],
      ),
    );
  }
}
