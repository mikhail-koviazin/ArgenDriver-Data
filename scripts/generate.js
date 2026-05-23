#!/usr/bin/env node
// Run after adding/editing questions: node scripts/generate.js
// Reads all questions/NNNN/question.json in order, builds questions.json + index.js

const fs = require("fs")
const path = require("path")

const ROOT = path.join(__dirname, "..")
const QUESTIONS_DIR = path.join(ROOT, "questions")

const folders = fs
  .readdirSync(QUESTIONS_DIR)
  .filter((f) => /^\d{4}$/.test(f))
  .sort()

const questionsData = []
const imageRequires = []

for (const folder of folders) {
  const folderPath = path.join(QUESTIONS_DIR, folder)
  const questionFile = path.join(folderPath, "question.json")

  if (!fs.existsSync(questionFile)) continue

  questionsData.push(JSON.parse(fs.readFileSync(questionFile, "utf8")))

  const files = fs.readdirSync(folderPath)
  const imageFile = files.find((f) => /^b\d+\.jpg$/i.test(f))
  if (imageFile) {
    const key = imageFile.replace(/\.jpg$/i, "")
    imageRequires.push(`  ${key}: require('./questions/${folder}/${imageFile}')`)
  }
}

// Write merged questions.json (single file for fast dev-mode loading)
fs.writeFileSync(
  path.join(ROOT, "questions.json"),
  JSON.stringify(questionsData, null, 2),
  "utf8"
)

// Write index.js (1 JSON require + N image requires)
const indexOutput = `// AUTO-GENERATED — do not edit manually. Run: node scripts/generate.js
module.exports = {
  questions: require('./questions.json'),
  questionImages: {
${imageRequires.join(",\n")}
  },
}
`
fs.writeFileSync(path.join(ROOT, "index.js"), indexOutput, "utf8")

console.log(
  `Generated: questions.json (${questionsData.length} questions), index.js (${imageRequires.length} images)`
)
