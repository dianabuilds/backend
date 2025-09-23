import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import importPlugin from 'eslint-plugin-import';
import reactPlugin from 'eslint-plugin-react';
import jsxA11y from 'eslint-plugin-jsx-a11y';

const reactRecommended = reactPlugin.configs.recommended ?? { rules: {} };
const reactJsxRuntime = reactPlugin.configs['jsx-runtime'] ?? { rules: {} };
const jsxA11yRecommended = jsxA11y.configs.recommended ?? { rules: {} };

export default tseslint.config(
  {
    ignores: [
      'dist',
      'vendor/**',
      'ts/demo/**',
      'src/app/**',
      'src/components/**',
      'src/assets/**',
      'src/styles/**',
      'src/i18n/**',
      'src/configs/**',
      'src/constants/**',
      'src/hooks/**',
      'src/utils/**',
      'src/@types/**',
    ],
  },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
    },
    plugins: {
      react: reactPlugin,
      'jsx-a11y': jsxA11y,
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      import: importPlugin,
    },
    settings: {
      react: { version: 'detect' },
    },
    rules: {
      ...reactRecommended.rules,
      ...reactJsxRuntime.rules,
      ...jsxA11yRecommended.rules,
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': [
        'warn',
        { allowConstantExport: true },
      ],
      '@typescript-eslint/no-explicit-any': 'off',
      'no-empty': ['error', { allowEmptyCatch: true }],
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            '**/vendor/**',
            'apps/web/vendor/**',
            '../vendor/**',
            '@mui/*',
            'antd',
            '@chakra-ui/*',
            'react-bootstrap',
            'bootstrap',
            'react-icons',
            'react-icons/*',
            'tabler-icons-react',
            '@fortawesome/*',
          ],
          paths: [
            { name: '@heroicons/react', message: 'Import icons via src/shared/icons only' },
          ],
        },
      ],
      'react/react-in-jsx-scope': 'off',
      'react/jsx-uses-react': 'off',
      'react/prop-types': 'off',
      'react/display-name': 'off',
      'jsx-a11y/label-has-associated-control': 'off',
      'jsx-a11y/no-static-element-interactions': 'off',
      'jsx-a11y/click-events-have-key-events': 'off',
      'jsx-a11y/anchor-is-valid': 'off',
      'jsx-a11y/aria-role': 'off',
      'react/no-unescaped-entities': 'off',
      '@next/next/no-img-element': 'off',
    },
  },
);





