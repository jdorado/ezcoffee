import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtemp, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const pluginRoot = dirname(dirname(fileURLToPath(import.meta.url)));
const cliPath = join(pluginRoot, 'bin', 'coffee.mjs');
const fetchStubPath = join(pluginRoot, 'test-support', 'fetch-stub.mjs');

function runCli(args, { context = null, fetchOutput = '', input = '' } = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [cliPath, ...args], {
      cwd: pluginRoot,
      env: {
        ...process.env,
        EZ_PLUGIN_CONTEXT: context === null ? '' : JSON.stringify(context),
        COFFEE_TEST_FETCH_OUTPUT: fetchOutput,
        NODE_OPTIONS: [process.env.NODE_OPTIONS, `--import=${fetchStubPath}`]
          .filter(Boolean)
          .join(' '),
      },
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('error', reject);
    child.on('close', (code, signal) => resolve({ code, signal, stdout, stderr }));
    child.stdin.end(input);
  });
}

async function fetchRequest(outputPath) {
  try {
    return JSON.parse(await readFile(outputPath, 'utf8'));
  } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}

function errorPayload(result) {
  assert.equal(result.code, 1, result.stderr);
  return JSON.parse(result.stderr);
}

test('help exposes only the three bounded writes', async () => {
  const result = await runCli(['--help']);

  assert.equal(result.code, 0, result.stderr);
  assert.match(result.stdout, /coffee coffee save/);
  assert.match(result.stdout, /coffee shot save/);
  assert.match(result.stdout, /coffee record delete/);
  assert.doesNotMatch(result.stdout, /profile|history|generate|list/i);
});

test('a command without Ez-scoped context fails before any API call', async () => {
  const result = await runCli([
    'coffee', 'save', '--input', '-', '--request-id', 'coffee-test',
  ], { input: '{}' });
  const payload = errorPayload(result);

  assert.equal(payload.error.code, 'cli_error');
  assert.match(payload.error.message, /scoped application context/);
});

test('valid coffee input is transported with only the Ez capability and typed options', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'coffee-plugin-test-'));
  const fetchOutput = join(directory, 'fetch.json');
  try {
    const coffee = { name: 'Offline contract fixture', brand: 'Test' };
    const result = await runCli([
      'coffee', 'save', '--input', '-', '--request-id', 'coffee-test',
      '--coffee-id', 'coffee_test', '--expected-revision', '3',
    ], {
      context: { api_base_url: 'https://coffee.test', capability: 'capability-test' },
      fetchOutput,
      input: JSON.stringify(coffee),
    });

    assert.equal(result.code, 0, result.stderr);
    assert.deepEqual(JSON.parse(result.stdout), { id: 'coffee_test', revision: 1, name: 'Stub' });
    assert.deepEqual(await fetchRequest(fetchOutput), {
      url: 'https://coffee.test/v1/agent/coffees/save',
      method: 'POST',
      headers: {
        authorization: 'Bearer capability-test',
        'content-type': 'application/json',
      },
      body: {
        ...coffee,
        coffee_id: 'coffee_test',
        expected_revision: 3,
        request_id: 'coffee-test',
      },
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('coffee input cannot smuggle CLI metadata into the API payload', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'coffee-plugin-test-'));
  const inputPath = join(directory, 'coffee.json');
  const fetchOutput = join(directory, 'fetch.json');
  try {
    await writeFile(inputPath, JSON.stringify({ name: 'invalid', request_id: 'smuggled' }));
    const result = await runCli([
      'coffee', 'save', '--input', inputPath, '--request-id', 'coffee-test',
    ], {
      context: { api_base_url: 'https://coffee.test', capability: 'capability-test' },
      fetchOutput,
    });
    const payload = errorPayload(result);

    assert.match(payload.error.message, /only the Coffee object/);
    assert.equal(await fetchRequest(fetchOutput), null);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('forbidden capability flags fail with no fetch', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'coffee-plugin-test-'));
  const fetchOutput = join(directory, 'fetch.json');
  try {
    const result = await runCli([
      'coffee', 'save', '--input', '-', '--request-id', 'coffee-test',
      '--capability', 'smuggled',
    ], {
      context: { api_base_url: 'https://coffee.test', capability: 'capability-test' },
      fetchOutput,
      input: JSON.stringify({ name: 'invalid' }),
    });
    const payload = errorPayload(result);

    assert.match(payload.error.message, /Unknown option/);
    assert.equal(await fetchRequest(fetchOutput), null);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});

test('shot input requires coffee_id and never fetches without it', async () => {
  const directory = await mkdtemp(join(tmpdir(), 'coffee-plugin-test-'));
  const fetchOutput = join(directory, 'fetch.json');
  try {
    const result = await runCli([
      'shot', 'save', '--input', '-', '--request-id', 'shot-test',
    ], {
      context: { api_base_url: 'https://coffee.test', capability: 'capability-test' },
      fetchOutput,
      input: JSON.stringify({ dose: 18 }),
    });
    const payload = errorPayload(result);

    assert.match(payload.error.message, /coffee_id/);
    assert.equal(await fetchRequest(fetchOutput), null);
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
});
