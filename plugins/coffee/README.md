# Coffee Ez plugin

This is the minimal EzCoffee domain plugin for Ez. It exposes three deterministic
writes: saving a coffee, saving a shot, and deleting a coffee or shot record in
the EzCoffee API. It contains no model loop, conversation reconstruction,
catalog reader, or record store.

Install the reviewed local package through the bound tenant launcher:

```sh
ez plugins inspect coffee --source /absolute/ezcoffee/plugins/coffee
ez plugins catalog-add coffee --source /absolute/ezcoffee/plugins/coffee --revision sha256:...
ez plugins install coffee
ez plugins start coffee
ez plugins status coffee
ez tools list
```

The plugin runs only from an EzCoffee application turn. Ez passes its own
`run.application.context.plugins.coffee` object to the one-shot command
container as `EZ_PLUGIN_CONTEXT` (`{api_base_url, capability}`); the CLI never
accepts account identity, capability, or API URL as arguments. `ez coffee --help`
is available after installation. The three commands are
`ez coffee coffee save`, `ez coffee shot save`, and
`ez coffee record delete`; a real mutation requires the EzCoffee API to issue
that scoped context and to be reachable from the plugin container. Ez plugin
containers are isolated from the agent workspace, so the agent streams its
authored artifact through stdin:

```sh
cat /absolute/path/coffee.json | ez coffee coffee save \
 --input - --request-id coffee-<unique-key>

cat /absolute/path/shot.json | ez coffee shot save \
 --input - --request-id shot-<unique-key>

ez coffee record delete \
 --kind coffee --id ID --expected-revision REV --request-id delete-<unique-key>

ez coffee doctor --json
```

Revising passes `--coffee-id` with `--expected-revision` (or `--shot-id`
with `--expected-revision`) together; creating omits both. The backend creates
at revision 0, requires the exact current revision on update, bumps by one,
and returns 409 when stale. Recipe reuse copies inputs only; planned tests are
not logged shots. See `SKILL.md`.

## Local verification

This plugin follows the local testing flow. It is currently a reviewed
local package, not a published npm product; do not publish it merely to test
authentication or packaging.

From this directory, run the offline checks before the Ez smoke:

```sh
npm test
npm run release:check
npm run verify
node bin/coffee.mjs --help
node bin/coffee.mjs doctor --json
```

Then inspect the exact source or tarball, install it through the bound Ez
executor, and verify `ez coffee --help` plus `ez coffee doctor --json`. A real
mutation additionally requires the EzCoffee API to issue scoped context; do not
attempt live backend writes without credentials. No network is used by the
offline checks.
