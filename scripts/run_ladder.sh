#!/bin/bash
# ul9060 corrected key ladder — runs on a GitHub-hosted runner (Azure AS8075 egress)
set -u
B="$HOME/b"
OUT="$B/ssh_gha.tsv"
SUM="$B/summary.tsv"
: > "$OUT"; : > "$SUM"
WINDOWS="${W:-3}"; SPACING="${S:-240}"
HOSTS_FILE="$B/keys/hosts.tsv"
mapfile -t HOSTS < <(awk -F'\t' 'NR>1 && $2 ~ /^[0-9]+\./ {print $2}' "$HOSTS_FILE" | sort -u)
mapfile -t USERS < <(awk -F'\t' 'NR>1{print $3}' "$HOSTS_FILE" | sort -u | grep -v '^$')
echo "hosts=${#HOSTS[@]} users=${USERS[*]} windows=$WINDOWS spacing=$SPACING utc=$(date -u +%FT%TZ)"
mapfile -t KEYS < <(ls "$B"/keys/k* 2>/dev/null)
echo "keys=${#KEYS[@]}"
chmod 600 "${KEYS[@]}" 2>/dev/null || true
echo "sha_bundle=$(sha256sum "$B/bundle.tgz" | cut -d' ' -f1)"
echo "whoami=$(id -un) host=$(hostname) ip=$(curl -s -m 8 https://api.ipify.org || echo n/a)"

probe_tcp() { timeout 4 bash -c "exec 3<>/dev/tcp/$1/$2" 2>/dev/null && echo OPEN || echo CLOSED; }
export -f probe_tcp 2>/dev/null || true

do_ssh() { # key host user
  k="$1"; h="$2"; u="$3"
  r=$(timeout 12 ssh -F /dev/null -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
      -o ConnectTimeout=6 -o BatchMode=yes -o NumberOfPasswordPrompts=0 \
      -o PreferredAuthentications=publickey \
      -o PubkeyAcceptedAlgorithms=+ssh-rsa,ssh-ed25519 \
      -o KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 \
      -o HostKeyAlgorithms=+ssh-rsa \
      -i "$k" "$u@$h" 'id; hostname -I; nvidia-smi -L 2>/dev/null | head -2' 2>&1)
  rc=$?
  if echo "$r" | grep -q 'uid='; then
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tSEAT\t$u\t$(basename $k)\t$(echo "$r" | tr '\n' '|' | cut -c1-200)"
  elif echo "$r" | grep -qi 'Permission denied'; then
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tPERMDENY\t$u\t$(basename $k)\t-"
  elif echo "$r" | grep -qi 'timed out\|Connection timed out\|Operation timed out'; then
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tTIMEOUT\t$u\t$(basename $k)\t-"
  elif [ $rc -eq 124 ]; then
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tTIMEOUT\t$u\t$(basename $k)\ttimeout-wrap"
  elif echo "$r" | grep -qi 'Connection refused'; then
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tREFUSED\t$u\t$(basename $k)\t-"
  else
    echo -e "$h\t22\t$(date -u +%FT%TZ)\tOTHER\t$u\t$(basename $k)\t$(echo "$r" | tr '\n' ' ' | cut -c1-120)"
  fi
}
export -f do_ssh

for w in $(seq 1 "$WINDOWS"); do
  TS=$(date -u +%FT%TZ)
  echo "### window $w start $TS" | tee -a "$OUT"
  # 1) TCP matrix on the widened port set, parallel
  printf '%s\n' "${HOSTS[@]}" | xargs -P 64 -I{} bash -c 'for p in 22 80 443 2375 8888 10250 6006 8188; do o=$(timeout 4 bash -c "exec 3<>/dev/tcp/{}/$p" 2>/dev/null && echo OPEN || echo CLOSED); echo -e "{}\t$p\t'"$(date -u +%FT%TZ)"'\tw'"$w"'\ttcp\t$o"; done' >> "$OUT" 2>/dev/null
  # 2) SSH ladder: every key x every host x users discovered, parallel
  : > "$B/combos.txt"
  for k in "${KEYS[@]}"; do for h in "${HOSTS[@]}"; do for u in ${USERS:-t19}; do echo "$k|$h|$u" >> "$B/combos.txt"; done; done; done
  echo "combos=$(wc -l < $B/combos.txt)"
  cat "$B/combos.txt" | xargs -P 64 -I{} bash -c 'IFS="|" read -r k h u <<< "{}"; do_ssh "$k" "$h" "$u"' >> "$B/ssh_w$w.tsv" 2>/dev/null
  echo "window $w ssh rows: $(wc -l < $B/ssh_w$w.tsv 2>/dev/null || echo 0)"
  cat "$B/ssh_w$w.tsv" >> "$OUT" 2>/dev/null
  # 3) negative controls
  cp "${KEYS[0]}" "$B/mut.key"; sed -i '2s/A/B/' "$B/mut.key" 2>/dev/null; chmod 600 "$B/mut.key"
  do_ssh "$B/mut.key" "${HOSTS[0]}" "${USERS:-t19}" | sed 's/^/CTRL_MUTKEY\t/' >> "$OUT"
  cp "${KEYS[0]}" "$B/open.key"; chmod 644 "$B/open.key"
  r=$(timeout 10 ssh -F /dev/null -o StrictHostKeyChecking=no -o BatchMode=yes -o ConnectTimeout=5 -i "$B/open.key" "${USERS:-t19}"@"${HOSTS[0]}" 'id' 2>&1)
  echo -e "CTRL_0644\t-\t$(date -u +%FT%TZ)\t$(echo "$r" | grep -qi 'UNPROTECTED' && echo REFUSED_0644 || echo other)\t-\topen.key\t$(echo "$r" | tr '\n' ' ' | cut -c1-80)" >> "$OUT"
  echo -e "CTRL_BOGUS_HOST\t192.0.2.1\t$(date -u +%FT%TZ)\t$(timeout 6 bash -c 'exec 3<>/dev/tcp/192.0.2.1/22' 2>/dev/null && echo OPEN || echo CLOSED_TCP)\t-\t-\tbogus" >> "$OUT"
  echo -e "CTRL_JUNK_PORT\t${HOSTS[0]}\t$(date -u +%FT%TZ)\t$(timeout 4 bash -c "exec 3<>/dev/tcp/${HOSTS[0]}/1" 2>/dev/null && echo OPEN || echo CLOSED_TCP)\t-\t-\tport1" >> "$OUT"
  # summary for this window
  echo "w$w $TS seats=$(grep -c $'\tSEAT\t' $OUT) permdeny=$(grep -c $'\tPERMDENY\t' $OUT) timeout=$(grep -c $'\tTIMEOUT\t' $OUT) refused=$(grep -c $'\tREFUSED\t' $OUT) tcpopen=$(grep -c $'\ttcp\tOPEN' $OUT)" | tee -a "$SUM"
  if [ "$w" -lt "$WINDOWS" ]; then sleep "$SPACING"; fi
done
echo "=== FINAL ==="
cat "$SUM"
echo "=== open tcp rows ==="
grep -P '\ttcp\tOPEN' "$OUT" | sort -u | head -60
echo "=== seats ==="
grep -P '\tSEAT\t' "$OUT" | head -20
echo "=== other/permdeny sample ==="
grep -P '\t(OTHER|PERMDENY)\t' "$OUT" | head -20
