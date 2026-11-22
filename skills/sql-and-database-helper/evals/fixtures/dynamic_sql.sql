SET @sql = CONCAT('SELECT id FROM ', @tbl, ' WHERE name = ''x''');
PREPARE s FROM @sql;
EXECUTE s;
SELECT id FROM users WHERE name = '' || :name || '';
SELECT format('SELECT id FROM %s WHERE a = 1', 'users');
SELECT id FROM t WHERE a = ${user_id};
SELECT id FROM t WHERE name = '{name}';
EXEC('SELECT id FROM users WHERE name = ''' + @name + '''');
