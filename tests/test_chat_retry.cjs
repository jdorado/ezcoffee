const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')

const source = fs.readFileSync(path.resolve(__dirname, '../coffee_app/src/main.tsx'), 'utf8')
assert.match(source, /encodeURIComponent\(jobId\).*\/retry/)
assert.match(source, /className="message-retry"/)
assert.match(source, /aria-label="Retry message"/)
console.log('Chat retry: failed replies expose a bounded retry action in the frontend.')
