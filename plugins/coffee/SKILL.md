# Coffee agent record writes

Stay inside the native Ez context and the exact artifact files named by
the owner. Do not search sibling repositories, installed plugin packages,
API source, MongoDB, or runtime logs to recover a schema or prior run. If a
canonical coffee id and revision are not present in native context, stop and
return structured feedback asking Ez to provide that context; never invent a
revision.

Three writes. Author the typed JSON and stream it:

```sh
cat /absolute/path/coffee.json | ez coffee coffee save \
  --input - \
  --request-id coffee-<unique-key> \
  [--coffee-id ID --expected-revision REV]

cat /absolute/path/shot.json | ez coffee shot save \
  --input - \
  --request-id shot-<unique-key> \
  [--shot-id ID --expected-revision REV]

ez coffee record delete \
  --kind coffee|shot --id ID --expected-revision REV \
  --request-id delete-<unique-key>
```

Use stdin (`--input -`) because Ez runs the plugin in an isolated container.

- `coffee save` takes one `Coffee` object (`name`, `brand`, `roast_date`,
  `notes`, `tag_color`, `archived`). Omit `--coffee-id` and
  `--expected-revision` when creating; pass both together when revising. The
  backend creates at revision 0, requires the exact current revision on
  update, bumps by one, and returns 409 when stale. Deleted records stay
  deleted; new shots refuse an archived coffee.
- `shot save` takes one `Shot` object with required `coffee_id`. Omit
  `--shot-id` and `--expected-revision` when creating; pass both together
  when revising. A `recorded_at` value must include a timezone; `target_yield_max_g`
  must be at least `target_yield_g`. A new `logged` shot without
  `recorded_at` is stamped by the backend.
- `record delete` takes no stdin. Pass `--kind`, `--id`,
  `--expected-revision`, and `--request-id` together.
- Recipe reuse copies inputs only: `dose`, `grind`, `paper`, `temp`,
  `water_temp_c`, `water_g`, `ice_g`, `bloom_seconds`, `target_yield_g`,
  `target_yield_max_g`, `pressure`, `basket`, `puck_screen`, plus `coffee_id`
  and `status` planned. Never copy measured outputs or tasting results
  (`yield_g`, `stop_yield_g`, `seconds`, `first_drip`, `rating`,
  `taste_balance`, `outcome`, `taste`, and similar). Planned tests are not
  logged shots.
- Do not put credentials, owner or tenant identifiers, API URLs, or
  capabilities in the artifact. Reuse a request ID only when retrying the
  exact same payload after an uncertain result.
