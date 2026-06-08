# F8 派单:foxtest 仓库自身 CI(交给执行 AI)

> 目标:为 foxtest 仓库建立 GitHub Actions,跑脚本单测 + 生成冒烟。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F1 已完成**(有 `tests/`);F5 若已加用例更好。
- 预检:`python -m pytest $ROOT/tests/ -q`(本地应全绿)

## 范围
- 新增 `$ROOT/.github/workflows/ci.yml`:
  - Python 3.10–3.13 矩阵;
  - 安装依赖(`pip install pytest jsonschema`,如有 requirements 则用之);
  - 跑 `pytest tests/`;
  - 冒烟:`validate_ir.py` 校验示例 + `codegen.py` 生成(不做浏览器回放,避免 CI 装浏览器的重量)。
- Actions 版本用最新(checkout@v4 / setup-python@v5)。

## 参考(可直接采用)
```yaml
name: CI
on:
  push: { branches: [ main ] }
  pull_request: { branches: [ main ] }
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix: { python-version: ['3.10','3.11','3.12','3.13'] }
      fail-fast: false
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '${{ matrix.python-version }}', cache: pip }
      - run: pip install pytest jsonschema
      - run: pytest tests/ -q
      - name: codegen 冒烟
        run: |
          python skills/foxtest/scripts/validate_ir.py skills/foxtest/ir/examples/*.ir.json
          python skills/foxtest/scripts/codegen.py skills/foxtest/ir/examples/*.ir.json --lang both --out /tmp/smoke
```

## DoD 验收
```bash
python -c "import yaml; yaml.safe_load(open('$ROOT/.github/workflows/ci.yml')); print('YAML 合法')"
# 本地模拟 CI 步骤
pip install pytest jsonschema
python -m pytest $ROOT/tests/ -q
python $S/scripts/validate_ir.py $S/ir/examples/*.ir.json
python $S/scripts/codegen.py $S/ir/examples/*.ir.json --lang both --out /tmp/smoke
```
**通过标准:**
- [ ] `ci.yml` YAML 合法
- [ ] 本地按 CI 步骤跑:`tests/` 全绿 + 校验 + codegen 冒烟成功
- [ ] CI 不依赖真实浏览器(回放留给本地/后续专门 job)

## 交付物
1. `$ROOT/.github/workflows/ci.yml`
2. DoD 输出 + 勾选
