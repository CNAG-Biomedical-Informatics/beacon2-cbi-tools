import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Beacon v2 CBI Tools Docs',
  tagline: 'Documentation for preparing Beacon v2 deployments with Beacon Friendly Format data',
  favicon: 'img/logo.png',
  url: 'https://cnag-biomedical-informatics.github.io',
  baseUrl: '/beacon2-cbi-tools/',
  organizationName: 'CNAG-Biomedical-Informatics',
  projectName: 'beacon2-cbi-tools',
  onBrokenLinks: 'throw',
  i18n: {
    defaultLocale: 'en',
    locales: ['en'],
  },
  presets: [
    [
      'classic',
      {
        docs: {
          sidebarPath: './sidebars.ts',
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
      } satisfies Preset.Options,
    ],
  ],
  themeConfig: {
    image: 'img/logo.png',
    colorMode: {
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: 'Beacon v2 CBI Tools',
      logo: {
        alt: 'Beacon v2 CBI Tools',
        src: 'img/logo.png',
      },
      items: [
        {
          type: 'docSidebar',
          sidebarId: 'docsSidebar',
          position: 'left',
          label: 'Docs',
        },
        {
          to: '/docs/getting-started/quick-start',
          label: 'Quick Start',
          position: 'left',
        },
        {
          to: '/docs/getting-started/installation',
          label: 'Install',
          position: 'left',
        },
        {
          to: '/docs/troubleshooting/faq',
          label: 'FAQ',
          position: 'left',
        },
        {
          href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools',
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
            {
              label: 'Overview',
              to: '/docs/overview',
            },
            {
              label: 'Installation',
              to: '/docs/getting-started/installation',
            },
            {
              label: 'FAQ',
              to: '/docs/troubleshooting/faq',
            },
          ],
        },
        {
          title: 'Project',
          items: [
            {
              label: 'Repository',
              href: 'https://github.com/CNAG-Biomedical-Informatics/beacon2-cbi-tools',
            },
            {
              label: 'CNAG',
              href: 'https://www.cnag.eu',
            },
          ],
        },
      ],
      copyright: 'Copyright © 2023-2026 Manuel Rueda, CNAG.',
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
