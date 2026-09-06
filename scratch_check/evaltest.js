const fs = require('fs');
const src = fs.readFileSync('scratch_check/check.js', 'utf8');
try {
  const fn = eval(src);
  console.log('eval OK, typeof:', typeof fn);
} catch (e) {
  console.log('eval FAILED:', e.message);
}
