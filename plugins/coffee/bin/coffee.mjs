#!/usr/bin/env node

// Coffee exposes three explicit writes to Ez: coffee save, shot save, and
// record delete. The agent owns the surrounding context; these commands only
// transport typed artifacts to EzCoffee's authoritative API.

import { readFile } from 'node:fs/promises';

const VERSION = '0.1.0';

function fail(message) {
  const payload = message && typeof message === 'object' && message.payload
    ? message.payload
    : { error: { code: 'cli_error', message: message instanceof Error ? message.message : String(message) } };
  process.stderr.write(`${JSON.stringify(payload)}\n`);
  process.exitCode = 1;
}

class ApiError extends Error {
  constructor(payload) {
    super(payload?.error?.message || 'Coffee API request failed');
    this.payload = payload;
  }
}

function usage() {
  return `Coffee native agent tool

Write:
  coffee coffee save --input FILE|- --request-id KEY \\
    [--coffee-id ID --expected-revision REV]

  coffee shot save --input FILE|- --request-id KEY \\
    [--shot-id ID --expected-revision REV]

  coffee record delete --kind coffee|shot --id ID --expected-revision REV --request-id KEY

  coffee doctor --json

The coffee input is one Coffee object. The shot input is one Shot object with coffee_id. Do not include
owner, tenant, API URL, capability, request_id, or conversation content.`;
}

function parseOptions(args, allowed) {
  const values = {};
  for (let index = 0; index < args.length; index += 2) {
    const name = args[index];
    if (!allowed.has(name)) throw new Error(`Unknown option ${name}`);
    if (Object.hasOwn(values, name)) throw new Error(`${name} may be supplied only once`);
    const value = args[index + 1];
    if (!value || value.startsWith('--')) throw new Error(`${name} requires a value`);
    values[name] = value;
  }
  return values;
}

function optional(options, name) {
  return options[name];
}

function required(options, name) {
  const value = optional(options, name);
  if (!value) throw new Error(`${name} is required`);
  return value;
}

function parseRevision(value) {
  if (!/^\d+$/.test(value)) throw new Error('--expected-revision must be a non-negative integer');
  return Number(value);
}

async function runContext() {
  let coffee;
  try {
    coffee = JSON.parse(process.env.EZ_PLUGIN_CONTEXT || 'null');
  } catch {
    throw new Error('Ez supplied invalid Coffee plugin context');
  }
  if (!coffee || typeof coffee.api_base_url !== 'string' || typeof coffee.capability !== 'string') {
    throw new Error('This Coffee plugin has no scoped application context. Start from EzCoffee chat or mini-chat.');
  }
  return coffee;
}

async function call(context, method, path, body) {
  const response = await fetch(`${context.api_base_url}/v1/agent${path}`, {
    method,
    headers: {
      authorization: `Bearer ${context.capability}`,
      ...(body === undefined ? {} : { 'content-type': 'application/json' }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let parsed = null;
  try { parsed = text ? JSON.parse(text) : null; } catch { parsed = text; }
  if (!response.ok) {
    const detail = typeof parsed === 'object' && parsed !== null
      ? parsed
      : { detail: { message: text || 'request failed' } };
    const message = typeof detail.detail === 'string'
      ? detail.detail
      : detail.detail?.message || detail.message || detail.error?.message || text || 'request failed';
    throw new ApiError({
      error: {
        status: response.status,
        message: `Coffee API ${response.status}: ${message}`,
        ...detail,
      },
    });
  }
  return parsed;
}

async function jsonFile(file) {
  let parsed;
  try {
    const source = file === '-' ? await readStdin() : await readFile(file, 'utf8');
    parsed = JSON.parse(source);
  }
  catch (error) { throw new Error(`Could not read JSON input ${file}: ${error.message}`); }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error(`${file} must contain one JSON object`);
  return parsed;
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  return Buffer.concat(chunks).toString('utf8');
}

const COFFEE_FORBIDDEN = [
  'request_id', 'expected_revision', 'revision',
  'coffee_id', 'shot_id', 'id',
  'owner', 'tenant', 'account_id',
  'api_url', 'api_base_url', 'capability', 'token', 'url',
];

const SHOT_FORBIDDEN = COFFEE_FORBIDDEN.filter((field) => field !== 'coffee_id');

async function coffeeFile(file) {
  const parsed = await jsonFile(file);
  for (const field of COFFEE_FORBIDDEN) {
    if (Object.hasOwn(parsed, field)) throw new Error(`${file} must contain only the Coffee object; pass ${field} as a CLI option`);
  }
  for (const field of ['owner', 'tenant', 'capability', 'url', 'api_url', 'api_base_url']) {
    if (Object.hasOwn(parsed, field)) throw new Error(`${file} must not include ${field}; use native context only`);
  }
  return parsed;
}

async function shotFile(file) {
  const parsed = await jsonFile(file);
  for (const field of SHOT_FORBIDDEN) {
    if (Object.hasOwn(parsed, field)) throw new Error(`${file} must contain only the Shot object; pass ${field} as a CLI option`);
  }
  if (typeof parsed.coffee_id !== 'string' || !parsed.coffee_id) {
    throw new Error(`${file} must contain one Shot object with coffee_id`);
  }
  return parsed;
}

async function main() {
  const args = process.argv.slice(2);
  if (!args.length || args.includes('--help') || args.includes('-h')) {
    process.stdout.write(`${usage()}\n`);
    return;
  }
  const [area, action, ...rest] = args;
  if (area === 'doctor') {
    if (action === '--json' && rest.length === 0) {
      let hasContext = false;
      try {
        const context = await runContext();
        hasContext = Boolean(context.api_base_url && context.capability);
      } catch {
        hasContext = false;
      }
      process.stdout.write(`${JSON.stringify({ ok: true, plugin: 'coffee', version: VERSION, has_context: hasContext })}\n`);
      return;
    }
    throw new Error('Usage: coffee doctor --json');
  }
  const context = await runContext();
  let result;
  if (area === 'coffee' && action === 'save') {
    const options = parseOptions(rest, new Set(['--input', '--request-id', '--coffee-id', '--expected-revision']));
    const input = required(options, '--input');
    const requestId = required(options, '--request-id');
    const coffeeId = optional(options, '--coffee-id');
    const expectedRevision = optional(options, '--expected-revision');
    if (Boolean(coffeeId) !== Boolean(expectedRevision)) {
      throw new Error('Pass --coffee-id and --expected-revision together when revising; omit both when creating.');
    }
    result = await call(context, 'POST', '/coffees/save', {
      ...await coffeeFile(input),
      coffee_id: coffeeId || null,
      expected_revision: expectedRevision === undefined ? null : parseRevision(expectedRevision),
      request_id: requestId,
    });
  } else if (area === 'shot' && action === 'save') {
    const options = parseOptions(rest, new Set(['--input', '--request-id', '--shot-id', '--expected-revision']));
    const input = required(options, '--input');
    const requestId = required(options, '--request-id');
    const shotId = optional(options, '--shot-id');
    const expectedRevision = optional(options, '--expected-revision');
    if (Boolean(shotId) !== Boolean(expectedRevision)) {
      throw new Error('Pass --shot-id and --expected-revision together when revising; omit both when creating.');
    }
    result = await call(context, 'POST', '/shots/save', {
      ...await shotFile(input),
      shot_id: shotId || null,
      expected_revision: expectedRevision === undefined ? null : parseRevision(expectedRevision),
      request_id: requestId,
    });
  } else if (area === 'record' && action === 'delete') {
    const options = parseOptions(rest, new Set(['--kind', '--id', '--expected-revision', '--request-id']));
    const kind = required(options, '--kind');
    if (kind !== 'coffee' && kind !== 'shot') throw new Error('--kind must be coffee or shot');
    const id = required(options, '--id');
    const expectedRevision = parseRevision(required(options, '--expected-revision'));
    const requestId = required(options, '--request-id');
    result = await call(context, 'POST', '/records/delete', {
      kind,
      id,
      expected_revision: expectedRevision,
      request_id: requestId,
    });
  } else {
    throw new Error('Unknown Coffee command. Run coffee --help.');
  }
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

main().catch((error) => fail(error));
