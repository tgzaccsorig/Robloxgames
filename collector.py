name: Update Roblox Games

on:
  workflow_dispatch:
  schedule:
    - cron: "0 */6 * * *"

permissions:
  contents: write

jobs:
  update:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.x"

      - name: Run collector
        run: python collector.py

      - name: Save games.json
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

          git add games.json

          if git diff --cached --quiet; then
            echo "games.json не изменился"
          else
            git commit -m "Update Roblox games"
            git push
          fi
