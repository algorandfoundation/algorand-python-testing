import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const distRoot = path.join(docsRoot, 'dist')
const configPath = path.join(docsRoot, 'legacy-routes.json')

const config = JSON.parse(fs.readFileSync(configPath, 'utf8'))

const ensureDir = (filePath) => fs.mkdirSync(path.dirname(filePath), { recursive: true })

const renderRedirectHtml = (target) => `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Redirecting...</title>
  <meta http-equiv="refresh" content="0; url=${target}" />
  <link rel="canonical" href="${target}" />
</head>
<body>
  <p>Redirecting to <a href="${target}">${target}</a>.</p>
  <script>window.location.replace(${JSON.stringify(target)});</script>
</body>
</html>
`

const writeRedirect = (fromRelativePath, toRelativePath) => {
  const normalizedTo = toRelativePath.startsWith('/') ? toRelativePath.slice(1) : toRelativePath
  const target = `${config.basePath}${normalizedTo}`.replace(/\/\/+/g, '/')
  const targetHtml = renderRedirectHtml(target)
  const outPath = path.join(distRoot, fromRelativePath)
  ensureDir(outPath)
  fs.writeFileSync(outPath, targetHtml)
}

const walkFiles = (dir, acc = []) => {
  if (!fs.existsSync(dir)) return acc

  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const entryPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walkFiles(entryPath, acc)
      continue
    }
    acc.push(entryPath)
  }
  return acc
}

for (const route of config.routes) {
  writeRedirect(route.from, route.to)
}

for (const family of config.families) {
  const familyTargetRoot = path.join(distRoot, family.toPrefix)
  const canonicalFiles = walkFiles(familyTargetRoot).filter((file) => file.endsWith(path.join('', 'index.html')))

  for (const canonicalFile of canonicalFiles) {
    const relativeToFamily = path
      .relative(familyTargetRoot, path.dirname(canonicalFile))
      .split(path.sep)
      .join('/')

    const fromRelativePath = relativeToFamily
      ? `${family.fromPrefix}${relativeToFamily}${family.fromExtension}`
      : `${family.fromPrefix}index${family.fromExtension}`

    const toRelativePath = relativeToFamily
      ? `${family.toPrefix}${relativeToFamily}/`
      : `${family.toPrefix}`

    if (fromRelativePath === `${family.toPrefix}index.html`) {
      continue
    }

    writeRedirect(fromRelativePath, toRelativePath)
  }
}

process.stdout.write('Generated legacy redirect shims\n')
