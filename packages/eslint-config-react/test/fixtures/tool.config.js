import { readFileSync } from 'node:fs';

export default {
  name: readFileSync(new URL('./package.json', import.meta.url), 'utf8').length > 0 ? 'ok' : 'empty',
  cwd: process.cwd(),
};
