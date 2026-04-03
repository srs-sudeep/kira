import { themes as prismThemes } from 'prism-react-renderer';
import type { Config } from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'KIRA Platform',
  tagline: 'Hotel Channel Manager — Developer Documentation',
  favicon: 'img/favicon.ico',

  url: 'https://docs.kira.abodeab.com',
  baseUrl: '/',

  organizationName: 'abodeab',
  projectName: 'kira',

  onBrokenLinks: 'throw',
  onBrokenMarkdownLinks: 'warn',

  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },

  markdown: {
    mermaid: true,
  },

  themes: ['@docusaurus/theme-mermaid'],

  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/abodeab/kira/tree/main/docs-site/',
          showLastUpdateAuthor: true,
          showLastUpdateTime: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: 'img/kira-social-card.png',
    colorMode: {
      defaultMode: 'light',
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'KIRA Docs',
      logo: {
        alt: 'KIRA Logo',
        src: 'img/logo.svg',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'mainSidebar',
          position: 'left',
          label: 'Documentation',
        },
        {
          href: 'https://github.com/abodeab/kira',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Docs',
          items: [
            { label: 'Getting Started', to: '/docs/' },
            { label: 'Architecture', to: '/docs/architecture/overview' },
            { label: 'API Reference', to: '/docs/api-reference/overview' },
          ],
        },
        {
          title: 'Services',
          items: [
            { label: 'Identity Service', to: '/docs/services/identity-service' },
            { label: 'Rate & Inventory', to: '/docs/services/rate-inventory-service' },
            { label: 'Channel Engine', to: '/docs/services/channel-engine' },
          ],
        },
        {
          title: 'More',
          items: [
            { label: 'Deployment', to: '/docs/deployment/overview' },
            { label: 'Operations', to: '/docs/operations/monitoring' },
            { label: 'Contributing', to: '/docs/contributing/development-setup' },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} Abode@AB. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['python', 'typescript', 'bash', 'yaml', 'sql', 'json', 'docker'],
    },
    mermaid: {
      theme: { light: 'neutral', dark: 'dark' },
    },
    algolia: undefined,
  } satisfies Preset.ThemeConfig,
};

export default config;
