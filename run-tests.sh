#!/usr/bin/env bash

set -uo pipefail

failures=()

echo "Running backend pytest suite..."
if ! docker compose run --rm backend pytest backend/test/ -v; then
  failures+=("backend pytest")
else
  echo "Backend pytest completed successfully."
fi

echo "Running Playwright E2E suite..."
if ! (cd test && npx playwright test); then
  failures+=("Playwright E2E")
else
  echo "Playwright E2E completed successfully."
fi

if [ ${#failures[@]} -eq 0 ]; then
  echo "All test suites passed."
  exit 0
fi

printf 'The following test suites failed: %s\n' "${failures[*]}"
exit 1
