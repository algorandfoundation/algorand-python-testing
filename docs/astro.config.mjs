// @ts-check
import { defineConfig } from 'astro/config'
import starlight from '@astrojs/starlight'
import remarkGithubAlerts from 'remark-github-alerts'
import sidebar from './sidebar.config.json'

export default defineConfig({
  site: 'https://algorandfoundation.github.io',
  base: '/algorand-python-testing/',
  trailingSlash: 'always',
  markdown: {
    remarkPlugins: [remarkGithubAlerts],
  },
  integrations: [
    starlight({
      title: 'Algorand Python Testing',
      favicon: '/algokit_logo.png',
      tableOfContents: { minHeadingLevel: 2, maxHeadingLevel: 4 },
      customCss: [
        './src/styles/api-reference.css',
        'remark-github-alerts/styles/github-colors-light.css',
        'remark-github-alerts/styles/github-colors-dark-media.css',
        'remark-github-alerts/styles/github-base.css',
      ],
      social: [
        {
          icon: 'github',
          label: 'GitHub',
          href: 'https://github.com/algorandfoundation/algorand-python-testing',
        },
        { icon: 'discord', label: 'Discord', href: 'https://discord.gg/algorand' },
      ],
      sidebar,
    }),
  ],
})
