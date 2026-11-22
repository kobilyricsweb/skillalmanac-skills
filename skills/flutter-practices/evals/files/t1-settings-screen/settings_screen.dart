import 'package:flutter/material.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  bool _loaded = false;
  bool _notifications = true;
  int _taps = 0;

  @override
  Widget build(BuildContext context) {
    if (!_loaded) {
      _loaded = true;
      setState(() {
        _notifications = true;
      });
    }
    print('settings built, taps=$_taps');
    return Scaffold(
      appBar: AppBar(title: Text('Settings')),
      body: ListView(
        children: [
          Padding(
            padding: EdgeInsets.all(16),
            child: Text('Preferences'),
          ),
          SwitchListTile(
            title: Text('Notifications'),
            value: _notifications,
            onChanged: (value) {
              setState(() {
                _notifications = value;
                _taps++;
              });
            },
          ),
          Divider(),
          ListTile(
            leading: Icon(Icons.info),
            title: Text('About'),
            onTap: () => Navigator.of(context).pushNamed('/about'),
          ),
        ],
      ),
    );
  }
}
