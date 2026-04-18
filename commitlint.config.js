export default {
  extends: ["@commitlint/config-conventional"],
  rules: {
    "scope-enum": [
      2,
      "always",
      [
        "identity",
        "admin",
        "rate-inventory",
        "reservation",
        "channel",
        "notification",
        "web",
        "infra",
        "docs",
        "shared",
        "cli",
        "deps",
        "docs-site",
      ],
    ],
  },
};
