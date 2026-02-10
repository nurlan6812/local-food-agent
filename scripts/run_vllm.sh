#!/bin/bash
# vLLM 서버 실행 스크립트

MODEL="LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct"
PORT=8081
MAX_MODEL_LEN=8192
GPU_MEMORY_UTILIZATION=0.85

echo "=== vLLM 서버 시작 ==="
echo "모델: $MODEL"
echo "포트: $PORT"
echo "최대 컨텍스트: $MAX_MODEL_LEN"
echo ""

# vLLM 서버 실행
vllm serve $MODEL \
    --port $PORT \
    --host 0.0.0.0 \
    --max-model-len $MAX_MODEL_LEN \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --trust-remote-code \
    --dtype auto \
    --api-key "local-vllm-key"

# 백그라운드 실행 원할 시:
# nohup vllm serve $MODEL --port $PORT --host 0.0.0.0 --max-model-len $MAX_MODEL_LEN --gpu-memory-utilization $GPU_MEMORY_UTILIZATION --trust-remote-code --dtype auto > /tmp/vllm.log 2>&1 &
