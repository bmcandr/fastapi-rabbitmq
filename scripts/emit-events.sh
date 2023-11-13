set -B                  # enable brace expansion
for i in {1..20}; do
    VAL=$((1 + $RANDOM % 10))
    curl -X 'GET' "http://localhost:8000/publish?message=${i}&duration=${VAL}"
done