import assert from 'node:assert/strict';
import { dirname, join } from 'node:path';
import { test } from 'node:test';
import { fileURLToPath } from 'node:url';
import { ESLint } from 'eslint';
import { reactConfig } from '../index.js';

const fixtures = join(dirname(fileURLToPath(import.meta.url)), 'fixtures');

async function lint(file, options = {}) {
  const eslint = new ESLint({
    cwd: fixtures,
    overrideConfigFile: true,
    overrideConfig: reactConfig({ tsconfigRootDir: fixtures, ...options }),
  });
  const [result] = await eslint.lintFiles([join(fixtures, file)]);
  return result.messages;
}

function ruleIds(messages) {
  return new Set(messages.map((m) => m.ruleId));
}

test('clean component passes with zero problems', async () => {
  const messages = await lint('good.tsx');
  assert.deepEqual(
    messages.map((m) => `${m.ruleId}: ${m.message}`),
    [],
  );
});

test('setState in useEffect is an error', async () => {
  const messages = await lint('bad-effect.tsx');
  const hit = messages.find((m) => m.ruleId === 'react-hooks/set-state-in-effect');
  assert.ok(hit, `expected set-state-in-effect, got ${[...ruleIds(messages)].join(', ')}`);
  assert.equal(hit.severity, 2);
});

test('effectRulesAsWarnings downgrades set-state-in-effect', async () => {
  const messages = await lint('bad-effect.tsx', { effectRulesAsWarnings: true });
  const hit = messages.find((m) => m.ruleId === 'react-hooks/set-state-in-effect');
  assert.ok(hit);
  assert.equal(hit.severity, 1);
});

test('TypeScript escape hatches and legacy React APIs are errors', async () => {
  const ids = ruleIds(await lint('bad-ts.tsx'));
  for (const rule of [
    '@typescript-eslint/no-explicit-any',
    '@typescript-eslint/no-non-null-assertion',
    'no-restricted-syntax', // enum
    'no-restricted-imports', // forwardRef
    '@typescript-eslint/no-restricted-types', // React.FC
  ]) {
    assert.ok(ids.has(rule), `expected ${rule}, got ${[...ids].join(', ')}`);
  }
});

test('accessibility problems are reported', async () => {
  const ids = ruleIds(await lint('bad-a11y.tsx'));
  assert.ok(ids.has('jsx-a11y/alt-text'), [...ids].join(', '));
  assert.ok(ids.has('jsx-a11y/click-events-have-key-events'), [...ids].join(', '));
});

test('throws a helpful error without tsconfigRootDir', () => {
  assert.throws(() => reactConfig({}), /tsconfigRootDir/);
});

test('plain JS config files lint without type information', async () => {
  const messages = await lint('tool.config.js');
  assert.deepEqual(
    messages.map((m) => `${m.ruleId}: ${m.message}`),
    [],
  );
});
