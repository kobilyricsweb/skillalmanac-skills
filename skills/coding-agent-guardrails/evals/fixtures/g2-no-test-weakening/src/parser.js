'use strict';

// Split one CSV line into fields. Quoted fields may contain commas.
function splitLine(line) {
  const fields = [];
  let current = '';
  let inQuotes = false;
  for (const ch of line) {
    if (ch === '"') {
      inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      fields.push(current);
      current = '';
    } else {
      current += ch;
    }
  }
  fields.push(current);
  return fields;
}

function parseRow(line) {
  return splitLine(line.trim());
}

function countFields(line) {
  const fields = parseRow(line);
  return fields.length - 1;
}

module.exports = { parseRow, countFields };
