#!/bin/bash
set -e

echo "🚀 Push to PRIVATE repository"
echo "=============================="

# Weryfikacja repo
if [ ! -d .git ]; then
  echo "❌ Brak repozytorium git w bieżącym katalogu"
  exit 1
fi

echo "📍 Repo origin: $(git remote get-url origin 2>/dev/null || echo 'brak')"

echo ""
echo "🧹 Czyszczenie cache przed pushem (możesz pominąć: SKIP_CLEAN=1)"
if [ "${SKIP_CLEAN:-0}" != "1" ]; then
  # Usuwanie typowych cache w całym repo (w tym w .venv)
  # __pycache__
  find . -type d -name "__pycache__" -prune -exec rm -rf {} + 2>/dev/null || true
  # pliki .pyc/.pyo
  find . -type f \( -name "*.pyc" -o -name "*.pyo" \) -delete 2>/dev/null || true
  # katalogi narzędzi
  rm -rf .pytest_cache .mypy_cache .ruff_cache .cache 2>/dev/null || true
  echo "✅ Cache wyczyszczone"
else
  echo "⏭️  Pomijam czyszczenie cache (SKIP_CLEAN=1)"
fi

echo ""
echo "📋 Zmiany do zatwierdzenia (aktualny stan):"
git status --porcelain || true

echo ""
echo "🧮 Skanuję pliki ignorowane przez .gitignore, które ZOSTANĄ dołączone do commita..."
IGNORED_LIST=$(git ls-files -oi --exclude-standard -z || true)
IGNORED_COUNT=$(printf "%s" "$IGNORED_LIST" | tr '\0' '\n' | sed '/^$/d' | wc -l)
if [ "$IGNORED_COUNT" -gt 0 ]; then
  echo "⚠️  Znaleziono $IGNORED_COUNT ignorowanych plików, które zostaną dołączone (podgląd 20):"
  printf "%s" "$IGNORED_LIST" | tr '\0' '\n' | sed '/^$/d' | head -20 | while read -r f; do
    [ -e "$f" ] && du -h "$f" 2>/dev/null || echo "$f"
  done
else
  echo "✅ Brak ignorowanych plików do dołączenia"
fi

echo ""
read -p "🤔 Dodać WSZYSTKO łącznie z plikami ignorowanymi i wypchnąć na 'origin'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Anulowano push do private"
  exit 1
fi

# 1) Dodaj wszystkie zwykłe zmiany
git add -A

# 2) Wymuś dodanie plików ignorowanych
if [ "$IGNORED_COUNT" -gt 0 ]; then
  printf "%s" "$IGNORED_LIST" | xargs -0 -r git add -f --
fi

# 3) Jawnie dołącz .venv jeśli istnieje (na wypadek globalnych reguł ignorowania)
if [ -d ".venv" ]; then
  echo "ℹ️  Wymuszam dodanie katalogu .venv"
  git add -f .venv
fi

if git diff --cached --quiet; then
  echo "ℹ️  Brak zmian do commitowania"
else
  default_msg="Private full-sync (incl. ignored) $(date +%Y%m%d-%H%M)"
  read -p "📝 Podaj wiadomość commita [${default_msg}]: " commit_msg
  commit_msg=${commit_msg:-$default_msg}
  git commit -m "$commit_msg"
  echo "✅ Zmiany zacommitowane"
fi

read -p "🚀 Wypchnąć zmiany na 'origin'? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "❌ Anulowano push"
  exit 0
fi

git push origin HEAD
echo "✅ Push zakończony"

echo ""
echo "💡 Uwaga: Lokalne pliki *.deb NIE są usuwane ani commitowane (ignorowane przez .gitignore)."

