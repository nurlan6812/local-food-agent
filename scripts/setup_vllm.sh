#!/bin/bash
# vLLM 설치 및 EXAONE 모델 세팅 스크립트

echo "=== vLLM 설치 ==="
pip install vllm>=0.6.0

echo ""
echo "=== Hugging Face 로그인 (EXAONE 모델 다운로드용) ==="
echo "EXAONE 모델은 라이선스 동의가 필요합니다."
echo "1. https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct 방문"
echo "2. 라이선스 동의 후 Access 요청"
echo "3. huggingface-cli login 실행"
echo ""

# HF 토큰 확인
if [ -z "$HF_TOKEN" ]; then
    echo "HF_TOKEN 환경변수를 설정하거나 huggingface-cli login을 실행하세요."
fi

echo ""
echo "=== 모델 다운로드 테스트 ==="
python -c "
from huggingface_hub import snapshot_download
try:
    # 모델 정보만 확인 (전체 다운로드 X)
    from huggingface_hub import model_info
    info = model_info('LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct')
    print(f'모델 접근 가능: {info.id}')
    print(f'모델 크기: {info.safetensors.total / 1e9:.2f} GB')
except Exception as e:
    print(f'모델 접근 실패: {e}')
    print('HuggingFace에서 라이선스 동의가 필요합니다.')
"

echo ""
echo "=== 설치 완료 ==="
echo "서버 실행: ./scripts/run_vllm.sh"
