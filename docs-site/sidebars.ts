import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  mainSidebar: [
    "intro",
    {
      type: "category",
      label: "Getting Started",
      collapsed: false,
      items: [
        "getting-started/e2e-local-dev",
        "getting-started/prerequisites",
        "getting-started/local-setup",
        "getting-started/dev-dashboards",
        "getting-started/environment-variables",
        "getting-started/running-services",
        "getting-started/first-run",
        "getting-started/project-structure",
        "getting-started/cli-reference",
        "getting-started/makefile-and-cli",
        "getting-started/per-developer-db",
      ],
    },
    {
      type: "category",
      label: "Architecture",
      items: [
        "architecture/overview",
        "architecture/microservices",
        "architecture/communication",
        "architecture/multi-tenancy",
        "architecture/database-design",
        "architecture/event-driven",
        "architecture/security",
      ],
    },
    {
      type: "category",
      label: "Services",
      items: [
        "services/identity-service",
        "services/rate-inventory-service",
        "services/reservation-service",
        "services/channel-engine",
        "services/notification-service",
        "services/admin-service",
      ],
    },
    {
      type: "category",
      label: "Frontend",
      items: [
        "frontend/overview",
        "frontend/architecture",
        "frontend/state-management",
        "frontend/feature-modules",
      ],
    },
    {
      type: "category",
      label: "API Reference",
      items: [
        "api-reference/overview",
        "api-reference/authentication",
        "api-reference/rate-inventory",
        "api-reference/reservations",
        "api-reference/channels",
      ],
    },
    {
      type: "category",
      label: "Deployment",
      items: [
        "deployment/how-deployment-fits",
        "deployment/overview",
        "deployment/e2e-production",
        "deployment/local-docker",
        "deployment/aws-production",
        "deployment/kubernetes",
        "deployment/local-kubernetes",
        "deployment/cicd-pipeline",
        "deployment/ssl-and-domains",
        "deployment/deploy-scripts",
      ],
    },
    {
      type: "category",
      label: "Operations",
      items: [
        "operations/operations-cheat-sheet",
        "operations/monitoring",
        "operations/logging",
        "operations/alerting",
        "operations/backup-and-recovery",
        "operations/scaling",
        "operations/runbooks",
      ],
    },
    {
      type: "category",
      label: "Contributing",
      items: [
        "contributing/development-workflow",
        "contributing/git-hooks-and-pushes",
        "contributing/coding-standards",
        "contributing/adding-a-service",
        "contributing/adding-a-feature",
        "contributing/testing-guide",
        "contributing/commit-conventions",
      ],
    },
  ],
};

export default sidebars;
