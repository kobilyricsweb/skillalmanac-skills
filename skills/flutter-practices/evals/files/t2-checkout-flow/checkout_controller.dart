import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class CheckoutController {
  CheckoutController(this.context);

  final BuildContext context;
  Map<String, dynamic>? _cart;
  String? _orderId;

  Future<void> loadCart() async {
    final res = await http.get(Uri.parse('https://api.example.com/cart'));
    _cart = jsonDecode(res.body) as Map<String, dynamic>;
  }

  Future<void> trackEvent(String name) async {
    await http.post(Uri.parse('https://api.example.com/events'), body: name);
  }

  Future<void> submit() async {
    loadCart();
    trackEvent('submit');
    final total = _cart!['total'] as num;
    final items = _cart!['items'] as List;
    final res = await http.post(
      Uri.parse('https://api.example.com/orders'),
      body: jsonEncode({'total': total, 'count': items.length}),
    );
    _orderId = jsonDecode(res.body)['id'];
    Navigator.of(context).pushNamed('/done', arguments: _orderId!);
  }
}
