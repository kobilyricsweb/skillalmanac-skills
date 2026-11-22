import 'dart:async';

import 'package:http/http.dart' as http;

class Repo {
  Future<void> save(String id) async {
    await Future.delayed(const Duration(milliseconds: 10));
  }

  Future<void> dispose() async {}

  void load() {}

  Future<List<int>> fetchAll() async => [1, 2, 3];
}

class Controller {
  final Repo _repo = Repo();

  Future<void> refresh() async {
    await _repo.fetchAll();
  }

  void onTap() {
    _repo.save('a');
    refresh();
    Future.delayed(const Duration(seconds: 1));
    http.get(Uri.parse('https://example.com'));
    _repo.dispose();
    _repo.load();
    unawaited(_repo.save('b'));
    _repo.save('c').then((_) => null);
  }

  Future<void> onDone() async {
    await _repo.save('d');
    await refresh();
    final all = _repo.fetchAll();
    await all;
    if (all != null)
      refresh();
  }
}
