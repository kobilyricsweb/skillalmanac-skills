import 'package:flutter/material.dart';

// print('commented out') and setState(() {}) and Text('x') in a comment
/* block comment: print('x'); Text('y'); */

class Notes extends StatelessWidget {
  const Notes({super.key, required this.name});

  final String name;

  Widget build(BuildContext context) {
    const help = "Call print('x') or setState(() {}) in your code";
    final raw = r'\n print(1) Text("a")';
    final tpl = 'user: ${name}!';
    final apostrophe = "don't print";
    return Column(
      children: [
        Text('Hello $name'),
        Text(help),
        Text(raw + tpl + apostrophe),
        const Text('Already const'),
        Text('Real literal'),
      ],
    );
  }
}

void report() {
  print('real call');
}
