import Link from "@docusaurus/Link";
import useDocusaurusContext from "@docusaurus/useDocusaurusContext";
import Heading from "@theme/Heading";
import Layout from "@theme/Layout";
import clsx from "clsx";
import type { ReactNode } from "react";

type FeatureCard = {
  icon: string;
  title: string;
  description: string;
  href: string;
};

const FEATURE_CARDS: FeatureCard[] = [
  {
    icon: "🚀",
    title: "Getting Started",
    description:
      "Clone the repo, configure environment variables, and have all services running locally in minutes.",
    href: "/docs/getting-started/prerequisites",
  },
  {
    icon: "🏗️",
    title: "Architecture",
    description:
      "Deep dive into the microservices topology, multi-tenant data model, and Kafka event flow.",
    href: "/docs/architecture/overview",
  },
  {
    icon: "🔑",
    title: "Identity & Auth",
    description:
      "JWT authentication, RBAC roles, MFA setup, and audit logging across the platform.",
    href: "/docs/services/identity-service",
  },
  {
    icon: "📊",
    title: "Rate & Inventory",
    description:
      "Room types, rate plans, ARI calendar, restrictions, and bulk update APIs.",
    href: "/docs/services/rate-inventory-service",
  },
  {
    icon: "🔗",
    title: "Channel Engine",
    description:
      "OTA adapter architecture, ARI push/pull flows, sync retry strategy, and circuit breakers.",
    href: "/docs/services/channel-engine",
  },
  {
    icon: "☸️",
    title: "Deployment",
    description:
      "Docker Compose for local dev, Kubernetes with Kustomize overlays, and GitHub Actions CI/CD.",
    href: "/docs/deployment/overview",
  },
  {
    icon: "📡",
    title: "API Reference",
    description:
      "Complete REST API reference for all six microservices with request/response examples.",
    href: "/docs/api-reference/overview",
  },
  {
    icon: "📈",
    title: "Operations",
    description:
      "Prometheus metrics, Grafana dashboards, structured logging, and on-call runbooks.",
    href: "/docs/operations/monitoring",
  },
  {
    icon: "⚡",
    title: "CLI Tool",
    description:
      "Unified CLI for dev setup, testing, migrations, deployment, linting — all from one command.",
    href: "/docs/getting-started/cli-reference",
  },
];

function FeatureCardComponent({
  icon,
  title,
  description,
  href,
}: FeatureCard): ReactNode {
  return (
    <Link to={href} style={{ textDecoration: "none", color: "inherit" }}>
      <div className="feature-card">
        <div className="feature-card__icon">{icon}</div>
        <div className="feature-card__title">{title}</div>
        <p style={{ margin: 0, fontSize: "0.9rem", lineHeight: 1.5 }}>
          {description}
        </p>
      </div>
    </Link>
  );
}

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();

  return (
    <Layout title="Home" description={siteConfig.tagline}>
      {/* Hero */}
      <header className={clsx("hero hero--kira")}>
        <div className="container">
          <Heading as="h1" className="hero__title">
            KIRA Platform
          </Heading>
          <p className="hero__subtitle">
            Hotel Channel Manager — Developer Documentation
          </p>
          <p style={{ color: "rgba(255,255,255,0.75)", maxWidth: 600 }}>
            Multi-tenant SaaS platform for distributing room availability,
            rates, and inventory across Booking.com, Expedia, MakeMyTrip, and
            more — from a single dashboard.
          </p>
          <div
            style={{
              display: "flex",
              gap: "1rem",
              flexWrap: "wrap",
              marginTop: "1.5rem",
            }}
          >
            <Link
              className="button button--secondary button--lg"
              to="/docs/getting-started/prerequisites"
            >
              Get Started
            </Link>
            <Link
              className="button button--outline button--lg"
              style={{ color: "white", borderColor: "rgba(255,255,255,0.5)" }}
              to="/docs/architecture/overview"
            >
              Architecture Overview
            </Link>
          </div>
        </div>
      </header>

      {/* Quick-stats bar */}
      <div
        style={{
          background: "var(--kira-surface)",
          borderBottom: "1px solid var(--kira-border)",
          padding: "1rem 0",
        }}
      >
        <div className="container">
          <div
            style={{
              display: "flex",
              gap: "2rem",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            {[
              ["6", "Microservices"],
              ["3", "OTA Channels"],
              ["Python 3.13", "Backend"],
              ["React 19", "Frontend"],
              ["PostgreSQL 16", "Database"],
              ["Kafka", "Event Bus"],
            ].map(([value, label]) => (
              <div key={label} style={{ textAlign: "center" }}>
                <div
                  style={{
                    fontWeight: 700,
                    fontSize: "1.1rem",
                    color: "var(--ifm-color-primary)",
                  }}
                >
                  {value}
                </div>
                <div style={{ fontSize: "0.8rem", opacity: 0.7 }}>{label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Feature grid */}
      <main>
        <div className="container" style={{ padding: "3rem 0" }}>
          <Heading
            as="h2"
            style={{ textAlign: "center", marginBottom: "2rem" }}
          >
            Explore the Documentation
          </Heading>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
              gap: "1.25rem",
            }}
          >
            {FEATURE_CARDS.map((card) => (
              <FeatureCardComponent key={card.title} {...card} />
            ))}
          </div>
        </div>
      </main>
    </Layout>
  );
}
