// eslint.config.js
import js from "@eslint/js";
import pluginVue from "eslint-plugin-vue";
import prettierConfig from "@vue/eslint-config-prettier";

export default [
  {
    ignores: ["node_modules/", "dist/", "build/", "*.min.js", "coverage/"],
  },

  js.configs.recommended,

  ...pluginVue.configs["flat/recommended"],

  prettierConfig,

  {
    files: ["**/*.vue", "**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
    },
    rules: {
      "no-console": "warn",
      "no-debugger": "warn",
      "no-unused-vars": "warn",

      "vue/multi-word-component-names": "off",
      "vue/component-name-in-template-casing": ["error", "PascalCase"],
      "vue/no-mutating-props": "error",
      "vue/require-default-prop": "off",
      "vue/no-unused-components": "warn",

      "linebreak-style": "off",
    },
  },
];
