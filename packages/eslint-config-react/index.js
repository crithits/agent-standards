// @ts-check
import js from '@eslint/js';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';
import tseslint from 'typescript-eslint';

/**
 * Shared ESLint flat config for React + TypeScript repos.
 *
 * Usage (eslint.config.js):
 *   import { reactConfig } from '@crithits/eslint-config-react';
 *   export default reactConfig({ tsconfigRootDir: import.meta.dirname });
 *
 * @param {import('./index.d.ts').ReactConfigOptions} options
 * @returns {import('eslint').Linter.Config[]}
 */
export function reactConfig(options) {
  const { tsconfigRootDir, ignores = [], effectRulesAsWarnings = false } = options;

  if (!tsconfigRootDir) {
    throw new Error(
      '@crithits/eslint-config-react: pass { tsconfigRootDir: import.meta.dirname } so type-aware rules can find your tsconfig.',
    );
  }

  const effectSeverity = effectRulesAsWarnings ? 'warn' : 'error';

  return /** @type {import('eslint').Linter.Config[]} */ ([
    {
      name: 'crithits/ignores',
      ignores: ['**/dist/**', '**/build/**', '**/coverage/**', '**/.next/**', '**/*.gen.*', ...ignores],
    },

    js.configs.recommended,
    ...tseslint.configs.strictTypeChecked,
    ...tseslint.configs.stylisticTypeChecked,
    reactHooks.configs.flat.recommended,
    jsxA11y.flatConfigs.recommended,

    {
      name: 'crithits/base',
      languageOptions: {
        globals: { ...globals.browser },
        parserOptions: {
          projectService: true,
          tsconfigRootDir,
        },
      },
      linterOptions: {
        // Agents like to sprinkle eslint-disable comments; flag the stale ones.
        reportUnusedDisableDirectives: 'error',
      },
      rules: {
        // --- React: effects and purity (React Compiler rules) ---
        'react-hooks/set-state-in-effect': effectSeverity,
        'react-hooks/set-state-in-render': 'error',
        'react-hooks/exhaustive-deps': 'error',

        // --- TypeScript: no escape hatches ---
        '@typescript-eslint/no-explicit-any': 'error',
        '@typescript-eslint/no-non-null-assertion': 'error',
        '@typescript-eslint/consistent-type-assertions': [
          'error',
          { assertionStyle: 'as', objectLiteralTypeAssertions: 'never' },
        ],
        '@typescript-eslint/ban-ts-comment': [
          'error',
          {
            'ts-expect-error': 'allow-with-description',
            'ts-ignore': true,
            'ts-nocheck': true,
            minimumDescriptionLength: 10,
          },
        ],
        '@typescript-eslint/consistent-type-imports': ['error', { fixStyle: 'inline-type-imports' }],
        '@typescript-eslint/consistent-type-definitions': ['error', 'type'],
        '@typescript-eslint/switch-exhaustiveness-check': 'error',
        '@typescript-eslint/no-unused-vars': [
          'error',
          { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
        ],
        '@typescript-eslint/restrict-template-expressions': ['error', { allowNumber: true }],

        // --- Patterns we steer agents away from ---
        'no-restricted-syntax': [
          'error',
          {
            selector: 'TSEnumDeclaration',
            message: 'Use a string-literal union or an `as const` object instead of enum.',
          },
        ],
        'no-restricted-imports': [
          'error',
          {
            paths: [
              {
                name: 'react',
                importNames: ['forwardRef'],
                message: 'React 19: pass `ref` as a regular prop instead of forwardRef.',
              },
            ],
          },
        ],
        '@typescript-eslint/no-restricted-types': [
          'error',
          {
            types: {
              'React.FC': { message: 'Type props directly: function Foo(props: FooProps) {}' },
              'React.FunctionComponent': {
                message: 'Type props directly: function Foo(props: FooProps) {}',
              },
            },
          },
        ],
      },
    },

    {
      // Plain JS config files (eslint.config.js, vite.config.js, etc.) aren't type-checked.
      ...tseslint.configs.disableTypeChecked,
      name: 'crithits/js-files',
      files: ['**/*.{js,mjs,cjs}'],
      languageOptions: {
        ...tseslint.configs.disableTypeChecked.languageOptions,
        globals: { ...globals.node },
      },
    },

    {
      // Tests: relax a few rules that fight with mocking.
      name: 'crithits/tests',
      files: ['**/*.{test,spec}.{ts,tsx}', '**/test/**/*.{ts,tsx}'],
      rules: {
        '@typescript-eslint/no-non-null-assertion': 'off',
        '@typescript-eslint/unbound-method': 'off',
      },
    },
  ]);
}

export default reactConfig;
