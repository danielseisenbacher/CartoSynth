#!/usr/bin/env bash
# CartoSynth in Docker. Needs only Docker on the host.
#
#   ./cartosynth.sh build                      build the image (automatic on first use)
#   ./cartosynth.sh generate config/3la.yaml   generate a dataset (see --help)
#   ./cartosynth.sh check output/3la           verify a finished run
#   ./cartosynth.sh visualize output/3la       draw annotations onto some tiles
#   ./cartosynth.sh fonts --config ...         build custom fonts, check font styles
#   ./cartosynth.sh glyphs                     letter images -> glyph SVGs
#   ./cartosynth.sh words AT austria           download place names from OpenStreetMap
#   ./cartosynth.sh test                       run the test suite
#   ./cartosynth.sh shell                      interactive shell in the container
#
# The repository is mounted at /workspace and the container runs with your user id,
# so all outputs belong to you. Set CARTOSYNTH_IMAGE to use another image name.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE="${CARTOSYNTH_IMAGE:-cartosynth}"

build() {
    docker build -f "$REPO/docker/Dockerfile" -t "$IMAGE" "$REPO"
}

run() {
    local tty=()
    [ -t 0 ] && [ -t 1 ] && tty=(-it)
    docker run --rm "${tty[@]}" \
        --user "$(id -u):$(id -g)" -e HOME=/tmp \
        -v "$REPO":/workspace -w /workspace \
        "$IMAGE" "$@"
}

command="${1:-help}"
if [ "$command" = "build" ]; then
    build
    exit
fi
if [ "$command" = "help" ] || [ "$command" = "-h" ] || [ "$command" = "--help" ]; then
    sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'
    exit
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "Docker image '$IMAGE' not found, building it (once, ~5 min) ..."
    build
fi

case "$command" in
    shell) run bash ;;
    test)  shift; run python -m pytest -q tests "$@" ;;
    *)     run python -m cartosynth "$@" ;;
esac
