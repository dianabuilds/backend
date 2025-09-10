import js from '@eslint/js';
import globals from 'globals';
import react from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import eslintComments from 'eslint-plugin-eslint-comments';
import simpleImportSort from 'eslint-plugin-simple-import-sort';
import tseslint from 'typescript-eslint';
import { globalIgnores } from 'eslint/config';
import requireSanitizedDangerouslySetInnerHTML from './eslint/rules/require-sanitized-dangerously-set-inner-html.js';

// Flat config without "extends": include configs as separate items.
export default tseslint.config([
  // Ignore generated/build outputs and dependencies
  globalIgnores(['dist', 'node_modules', 'coverage', 'jscpd-report', 'jscpd-report-app']),

  // Base JS and framework configs
  js.configs.recommended,
  ...tseslint.configs.recommended,
  reactHooks.configs['recommended-latest'],
  reactRefresh.configs.vite,

  // Project rules for TS/TSX files
  {
    files: ['**/*.{ts,tsx}'],
    plugins: {
      'eslint-comments': eslintComments,
      react,
      'simple-import-sort': simpleImportSort,
      sanitizer: {
        rules: {
          'require-sanitized-dangerously-set-inner-html': requireSanitizedDangerouslySetInnerHTML,
        },
      },
    },
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    settings: {
      react: { version: 'detect' },
    },
    rules: {
      'eslint-comments/no-unused-disable': 'error',
      'react/jsx-key': 'error',
      'react/self-closing-comp': 'error',
      '@typescript-eslint/consistent-type-imports': 'error',
      // Allow top-of-file // @ts-nocheck (we gate fixes separately)
      '@typescript-eslint/ban-ts-comment': [
        'error',
        {
          'ts-expect-error': 'allow-with-description',
          'ts-ignore': 'allow-with-description',
          'ts-nocheck': false,
          'ts-check': false,
          minimumDescriptionLength: 6,
        },
      ],
      // Be pragmatic: report "any" as warning to avoid blocking
      '@typescript-eslint/no-explicit-any': ['warn', { ignoreRestArgs: true }],
      // Treat leading underscore as an opt-out for unused-var noise
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
      ],
      'simple-import-sort/imports': 'error',
      'simple-import-sort/exports': 'error',
      'sanitizer/require-sanitized-dangerously-set-inner-html': 'error',
      // Some regex literals intentionally escape quotes
      'no-useless-escape': 'warn',
    },
  },

  // Node/Tooling scripts (CJS)
  {
    files: ['scripts/**/*.{js,cjs}', '*.cjs', 'lint-staged.config.cjs'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.node,
      sourceType: 'script',
    },
    rules: {
      'no-undef': 'off',
      '@typescript-eslint/no-require-imports': 'off',
    },
  },

  // Soften strictness for generated OpenAPI models
  {
    files: ['src/openapi/**'],
    linterOptions: { reportUnusedDisableDirectives: false },
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
      'eslint-comments/no-unused-disable': 'off',
      'react-refresh/only-export-components': 'off',
    },
  },
]);
