import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class CleanPage extends StatefulWidget {
  const CleanPage({super.key, required this.title});

  final String title;

  @override
  State<CleanPage> createState() => _CleanPageState();
}

class _CleanPageState extends State<CleanPage> {
  int _count = 0;
  String? _note;

  Future<void> _load() async {
    await Future.delayed(const Duration(milliseconds: 10));
    if (!mounted) return;
    setState(() => _note = 'loaded');
  }

  @override
  void initState() {
    super.initState();
    unawaited(_load());
  }

  void _log(String message) {
    if (kDebugMode) {
      print(message);
    }
  }

  @override
  Widget build(BuildContext context) {
    final note = _note;
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Column(
        children: [
          const Text('You pressed the button'),
          const SizedBox(height: 8),
          Text('Count: $_count'),
          if (note != null) Text(note),
          ElevatedButton(
            onPressed: () {
              _log('add');
              setState(() {
                _count++;
              });
            },
            child: const Text('Add'),
          ),
          TextButton(
            onPressed: () => setState(() => _count = 0),
            child: const Text('Reset'),
          ),
        ],
      ),
    );
  }
}
