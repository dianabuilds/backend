import js from "@eslint/js";
import globals from "globals";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import eslintComments from "eslint-plugin-eslint-comments";
import simpleImportSort from "eslint-plugin-simple-import-sort";
import tseslint from "typescript-eslint";
import { globalIgnores } from "eslint/config";

export default tseslint.config([
  globalIgnores(["dist"]),
  {
    files: ["**/*.{ts,tsx}"],
    plugins: {
      "eslint-comments": eslintComments,
      react,
      "simple-import-sort": simpleImportSort,
    },
    extends: [
      js.configs.recommended,
      tseslint.configs.recommended,
      reactHooks.configs["recommended-latest"],
      reactRefresh.configs.vite,
    ],
    languageOptions: {
      ecmaVersion: 2020,
      globals: globals.browser,
    },
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      "eslint-comments/no-unused-disable": "error",
      "react/jsx-key": "error",
      "react/self-closing-comp": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "simple-import-sort/imports": "error",
      "simple-import-sort/exports": "error",
    },
  },
  {
    files: ["src/openapi/**"],
    linterOptions: {
      reportUnusedDisableDirectives: false,
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
      "eslint-comments/no-unused-disable": "off",
      "react-refresh/only-export-components": "off",
    },
  },
]);
