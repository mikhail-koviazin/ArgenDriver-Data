#!/usr/bin/env node
// Run after adding/editing questions: node scripts/generate.js
// Reads all questions/NNNN/question.json in order, builds index.js

const fs = require("fs")
const path = require("path")

const ROOT = path.join(__dirname, "..")
const QUESTIONS_DIR = path.join(ROOT, "questions")

const folders = fs
  .readdirSync(QUESTIONS_DIR)
  .filter((f) => /^\d{4}$/.test(f))
  .sort()

const questionRequires = []
const imageRequires = []

for (const folder of folders) {
  const folderPath = path.join(QUESTIONS_DIR, folder)
  const questionFile = path.join(folderPath, "question.json")

  if (!fs.existsSync(questionFile)) continue

  questionRequires.push(`  require('./questions/${folder}/question.json')`)

  const files = fs.readdirSync(folderPath)
  const imageFile = files.find((f) => /^b\d+\.jpg$/i.test(f))
  if (imageFile) {
    const key = imageFile.replace(/\.jpg$/i, "")
    imageRequires.push(`  ${key}: require('./questions/${folder}/${imageFile}')`)
  }
}

const output = `// AUTO-GENERATED — do not edit manually. Run: node scripts/generate.js
module.exports = {
  questions: [
${questionRequires.join(",\n")}
  ],
  questionImages: {
${imageRequires.join(",\n")}
  },
}
`

fs.writeFileSync(path.join(ROOT, "index.js"), output, "utf8")
console.log(`Generated index.js: ${questionRequires.length} questions, ${imageRequires.length} images`)
