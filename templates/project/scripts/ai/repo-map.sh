#!/usr/bin/env bash
set -euo pipefail

if ! command -v fd >/dev/null 2>&1; then
  printf 'repo-map.sh expects fd. Run the machine setup first.\n' >&2
  exit 1
fi

if ! command -v rg >/dev/null 2>&1; then
  printf 'repo-map.sh expects rg. Run the machine setup first.\n' >&2
  exit 1
fi

exclude_args=(
  -E .git
  -E node_modules
  -E target
  -E build
  -E dist
  -E coverage
  -E .next
  -E .gradle
  -E .idea
  -E .turbo
  -E vendor
)

glob_args=(
  --glob '!node_modules/**'
  --glob '!target/**'
  --glob '!build/**'
  --glob '!dist/**'
  --glob '!coverage/**'
  --glob '!.next/**'
  --glob '!.gradle/**'
  --glob '!.idea/**'
  --glob '!.git/**'
  --glob '!vendor/**'
)

echo '== Project signals =='
fd '^(go.mod|package.json|pnpm-workspace.yaml|bun.lockb|pyproject.toml|requirements.txt|Cargo.toml|build.gradle|build.gradle.kts|settings.gradle.kts|pom.xml|Dockerfile|docker-compose\.ya?ml|README\.md)$' . -d 2 -HI "${exclude_args[@]}" || true

echo
echo '== Top level =='
fd . . -d 2 -HI "${exclude_args[@]}" | head -200 || true

echo
echo '== Entrypoint candidates =='
fd '^(main|Main|server|app)\.(go|kt|kts|java|py|js|ts|tsx|rs)$' . -HI "${exclude_args[@]}" || true
rg -n 'func main\(|@SpringBootApplication|public static void main|http\.ListenAndServe|gin\.Default|echo\.New|FastAPI\(|Flask\(__name__\)|app\.listen\(|createServer\(' . "${glob_args[@]}" || true

echo
echo '== Routes / handlers =='
rg -n '@RequestMapping|@GetMapping|@PostMapping|@PutMapping|@DeleteMapping|router|route|HandleFunc|http\.Handle|gin\.|echo\.|mux\.|chi\.|FastAPI\(|APIRouter|Blueprint\(' . "${glob_args[@]}" || true

echo
echo '== Services / use cases =='
rg -n 'class .*Service|interface .*Service|type .*Service struct|func .*Service|usecase|UseCase' . "${glob_args[@]}" || true

echo
echo '== Persistence =='
rg -n 'Repository|Dao|JpaRepository|CrudRepository|sql\.DB|sqlx\.|gorm\.|ent\.|Exposed|RoomDatabase|@Entity|@Table' . "${glob_args[@]}" || true

echo
echo '== Config =='
fd '^(application|application-.*|config|settings|values|Chart)\.(ya?ml|properties|json|toml|env|ini)$' . -HI "${exclude_args[@]}" || true

echo
echo '== Tests =='
fd '(test|tests|__tests__|spec|specs)' . -HI "${exclude_args[@]}" || true

