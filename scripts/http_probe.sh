#!/bin/bash
set +u
OUT="$HOME/b/http_probe.txt"; : > "$OUT"
EP=("http://70.153.87.133" "http://134.149.59.33" "https://20.97.252.251" "https://20.125.42.21" "http://40.113.1.63:8080" "http://20.109.152.114" "https://20.109.152.114" "http://20.205.187.223" "http://40.123.206.138")
PATHS=("/" "/system_stats" "/v1/models" "/api/version" "/api/v1/version" "/openapi.json" "/jupyter" "/metrics" "/health" "/docs" "/api/kernelspecs")
echo "=== HTTP PROBE $(date -u +%FT%TZ) egress=$(curl -s -m 6 https://api.ipify.org)" | tee -a "$OUT"
for u in "${EP[@]}"; do
  base=$(echo "$u" | sed -E 's#(https?://[^/]+).*#\1#')
  for p in "${PATHS[@]}"; do
    r=$(curl -sk -m 6 -o /tmp/body.$$ -w '%{http_code} %{size_download} %{content_type}' "$base$p" 2>/dev/null)
    code=$(echo "$r" | awk '{print $1}')
    if [ "$code" != "000" ]; then
      echo -e "$base$p\t$r\t$(head -c 120 /tmp/body.$$ | tr -d '\n\r' | tr -c '[:print:]' '.')" >> "$OUT"
    fi
  done
  rm -f /tmp/body.$$
done
echo "=== DONE $(date -u +%FT%TZ)" | tee -a "$OUT"
cat "$OUT"
