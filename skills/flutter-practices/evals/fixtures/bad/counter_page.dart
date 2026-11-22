import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

class CounterPage extends StatefulWidget {
  const CounterPage({super.key});

  @override
  State<CounterPage> createState() => _CounterPageState();
}

class _CounterPageState extends State<CounterPage> {
  int _count = 0;
  bool _ready = false;

  void _increment() {
    print('incrementing');
    setState(() => _count++);
  }

  @override
  Widget build(BuildContext context) {
    if (!_ready) {
      setState(() {
        _ready = true;
      });
    }
    if (kDebugMode) {
      print('built with $_count');
    }
    debugPrint('plain debug line');
    return Scaffold(
      appBar: AppBar(title: Text('Counter')),
      body: Column(
        children: [
          Text('You pressed the button'),
          SizedBox(height: 8),
          Text('Count: $_count'),
          Icon(Icons.add, color: Colors.red[100]),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _count++;
              });
            },
            child: Text('Add'),
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
