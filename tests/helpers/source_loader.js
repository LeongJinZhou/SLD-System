'use strict';
const vm = require('node:vm');

// Compile only: extracting source must never run application startup or defaults.
function parses(code) {
  try { new vm.Script(code); return true; }
  catch (error) { if (error instanceof SyntaxError) return false; throw error; }
}

function createSourceLoader(source) {
  const cache = new Map();
  function start(kind, name) {
    if (!/^[A-Za-z_$][\w$]*$/.test(name)) throw Error(`Invalid declaration name: ${name}`);
    const keyword = kind === 'function' ? '(?:async[ \\t]+)?function\\s*\\*?' : kind;
    const pattern = new RegExp(`\\b${keyword}\\s+${name.replace(/\$/g, '\\$')}(?=[\\s(=,;])`, 'g');
    const matches = [...source.matchAll(pattern)].filter(match => {
      const prefix = source.slice(0, match.index);
      // A valid complete prefix establishes a top-level boundary; adding an
      // invalid token detects candidates hidden inside an unterminated // comment.
      return parses(prefix) && !parses(prefix + ' @');
    });
    if (matches.length !== 1) throw Error(`Expected one top-level ${kind} ${name}; found ${matches.length}`);
    return matches[0].index;
  }
  function extract(kind, name) {
    const key = `${kind} ${name}`;
    if (cache.has(key)) return cache.get(key);
    const begin = start(kind, name), endings = kind === 'function' ? /}/g : /;/g;
    endings.lastIndex = begin;
    for (let match; (match = endings.exec(source));) {
      const candidate = source.slice(begin, match.index + 1);
      // Parentheses prevent a closing brace inside a default/string/regex/template
      // from being mistaken for the end of a function declaration.
      if (parses(kind === 'function' ? `(${candidate}\n)` : candidate)) {
        cache.set(key, candidate);
        return candidate;
      }
    }
    throw Error(`No complete ${key} declaration`);
  }
  return {
    fn: name => extract('function', name),
    functions: names => names.map(name => extract('function', name)).join('\n'),
    declaration: (kind, name) => extract(kind, name),
    between(fromKind, fromName, toKind, toName) {
      const begin = start(fromKind, fromName), end = start(toKind, toName);
      if (end <= begin) throw Error(`Reversed source range: ${fromName} -> ${toName}`);
      const code = source.slice(begin, end);
      if (!parses(code)) throw Error(`Incomplete source range: ${fromName} -> ${toName}`);
      return code;
    },
    section(name) {
      if (!/^[A-Z_]+$/.test(name)) throw Error(`Invalid section name: ${name}`);
      const markers = suffix => [...source.matchAll(new RegExp(`^[ \\t]*//[ \\t]*${name}_${suffix}(?:[ \\t]+[^\\r\\n]*)?\\r?$`, 'gm'))]
        .filter(match => parses(source.slice(0, match.index)));
      const starts = markers('START'), ends = markers('END');
      if (starts.length !== 1 || ends.length !== 1 || ends[0].index <= starts[0].index)
        throw Error(`Expected one ordered ${name} START/END section`);
      const code = source.slice(starts[0].index + starts[0][0].length, ends[0].index);
      if (!parses(code)) throw Error(`Incomplete ${name} section`);
      return code;
    }
  };
}

module.exports = { createSourceLoader };
