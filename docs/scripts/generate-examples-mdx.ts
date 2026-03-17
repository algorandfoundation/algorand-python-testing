import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const repoRoot = path.resolve(docsRoot, '..')
const examplesRoot = path.join(repoRoot, 'examples')
const outputDir = path.join(docsRoot, 'src', 'content', 'docs', 'examples')
const repoUrl = 'https://github.com/algorandfoundation/algorand-python-testing/blob/main'

type ExamplePage = {
  slug: string
  title: string
  summary: string
  sourcePath: string
  testPath: string | null
}

const ensureDir = (dir: string) => fs.mkdirSync(dir, { recursive: true })

const toTitle = (value: string) =>
  value
    .split(/[-_]/g)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')

const firstModuleDocstring = (content: string): string | null => {
  const cleaned = content.replace(/^\s*#.*\n/gm, '').trimStart()
  const match = cleaned.match(/^(?:"""([\s\S]*?)"""|'''([\s\S]*?)''')/)
  if (!match) return null

  const raw = (match[1] ?? match[2] ?? '').trim()
  if (!raw) return null
  return raw.split(/\n\s*\n/)[0]?.replace(/\s+/g, ' ').trim() ?? null
}

const getMainModuleFile = (exampleDir: string): string | null => {
  const preferred = ['contract.py', 'signature.py', 'main.py']
  for (const name of preferred) {
    const candidate = path.join(exampleDir, name)
    if (fs.existsSync(candidate)) return candidate
  }

  const pythonFiles = fs
    .readdirSync(exampleDir)
    .filter((name) => name.endsWith('.py') && !name.startsWith('test_') && name !== '__init__.py')
    .sort()

  if (pythonFiles.length === 0) return null
  return path.join(exampleDir, pythonFiles[0])
}

const buildExamplePages = (): ExamplePage[] => {
  if (!fs.existsSync(examplesRoot)) return []

  const dirs = fs
    .readdirSync(examplesRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort()

  return dirs.map((dirName) => {
    const exampleDir = path.join(examplesRoot, dirName)
    const slug = dirName.replace(/_/g, '-')
    const title = toTitle(dirName)

    const moduleFile = getMainModuleFile(exampleDir)
    const sourcePath = moduleFile
      ? path.relative(repoRoot, moduleFile).replace(/\\/g, '/')
      : `examples/${dirName}`

    const testFile = fs
      .readdirSync(exampleDir)
      .filter((name) => /^test_.*\.py$/.test(name))
      .sort()[0]
    const testPath = testFile ? path.posix.join('examples', dirName, testFile) : null

    let summary = 'Example source and tests for this contract are available in the repository.'
    if (moduleFile) {
      const docstring = firstModuleDocstring(fs.readFileSync(moduleFile, 'utf8'))
      if (docstring) summary = docstring
    }

    return {
      slug,
      title,
      summary,
      sourcePath,
      testPath,
    }
  })
}

const renderExamplePage = (example: ExamplePage): string => {
  const testLink = example.testPath
    ? `- [Test file](${repoUrl}/${example.testPath})`
    : '- Test file not detected in this example directory.'

  return `---
title: ${example.title}
description: ${example.summary}
---

${example.summary}

## Repository links

- [Source file](${repoUrl}/${example.sourcePath})
${testLink}
`
}

const cleanOutput = () => {
  if (!fs.existsSync(outputDir)) return

  for (const entry of fs.readdirSync(outputDir)) {
    fs.rmSync(path.join(outputDir, entry), { recursive: true, force: true })
  }
}

const main = () => {
  ensureDir(outputDir)
  cleanOutput()

  const examples = buildExamplePages()

  for (const example of examples) {
    fs.writeFileSync(path.join(outputDir, `${example.slug}.mdx`), renderExamplePage(example))
  }

  process.stdout.write(`Generated ${examples.length} example page(s) in ${outputDir}\n`)
}

main()
