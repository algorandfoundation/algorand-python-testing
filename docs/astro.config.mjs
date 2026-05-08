// @ts-check
import { defineConfig } from 'astro/config'
import starlight from '@astrojs/starlight'
import remarkGithubAlerts from 'remark-github-alerts'
import sidebar from './sidebar.config.json'

export default defineConfig({
  site: 'https://algorandfoundation.github.io',
  base: '/algorand-python-testing/',
  trailingSlash: 'always',
  redirects: {
    '/testing-guide/': '/algorand-python-testing/concepts/overview/',
    '/testing-guide/concepts/': '/algorand-python-testing/concepts/test-context/',
    '/testing-guide/avm-types/': '/algorand-python-testing/concepts/avm-types/',
    '/testing-guide/arc4-types/': '/algorand-python-testing/concepts/arc4-types/',
    '/testing-guide/opcodes/': '/algorand-python-testing/concepts/opcodes/',
    '/testing-guide/contract-testing/': '/algorand-python-testing/guide/contract-testing/',
    '/testing-guide/signature-testing/': '/algorand-python-testing/guide/signature-testing/',
    '/testing-guide/state-management/': '/algorand-python-testing/guide/state-management/',
    '/testing-guide/subroutines/': '/algorand-python-testing/guide/subroutines/',
    '/testing-guide/transactions/': '/algorand-python-testing/guide/transactions/',
    '/coverage/': '/algorand-python-testing/reference/coverage/',
    '/faq/': '/algorand-python-testing/reference/faq/',
    '/algopy/': '/algorand-python-testing/concepts/algopy/',
    '/api/': '/algorand-python-testing/api/algopy_testing/',
  },
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
