# Sourced by the Tools scripts: exports the private settings from `.env` (kept out of git; copy
# `.env.example` to `.env` and fill it in). Variables already set in the environment win over the
# file, so CI passes its secrets as environment variables and needs no `.env`.
if [ -f .env ]; then
  while IFS='=' read -r key value; do
    [[ -z "$key" || "$key" == \#* ]] && continue
    [ -z "${!key:-}" ] && export "$key=$value"
  done < .env
fi
