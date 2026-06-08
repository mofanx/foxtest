# foxtest

**AI 驱动的 Web 自动化测试**:自然语言用例 → 浏览器探索 → 语言无关 IR → Playwright 脚本(Python + TypeScript)→ 多层覆盖度量。

本仓库同时是一个 **Claude Code plugin** 雏形:核心能力以 **Skill** 形态提供,可被支持 Agent Skills 的 agent(Claude / Devin / Windsurf 等)直接调用;未来加 `.claude-plugin/plugin.json`(已预置)即可作为 plugin 分发。

## 设计

```
NL/Markdown 用例 ──(AI + dp-cli 探索)──► IR(JSON,单一事实源)
                                            │
                          ┌─────────────────┴─────────────────┐
                          ▼                                     ▼
                Python(pytest+playwright)         TypeScript(@playwright/test)
```

- **AI 负责**:理解用例、探索页面、产出 IR(语义定位优先)。
- **脚本负责(确定性)**:IR → 双语言 codegen、schema 校验、覆盖计算。
- **浏览器能力**:复用 [dp-cli](https://github.com/mofanx/dp-cli)(snapshot 的 `ref:N` 提供语义感知)。

## 目录

```
.claude-plugin/plugin.json        # plugin 清单(未来分发用)
skills/foxtest/                    # Skill 本体(可 symlink 到 ~/.claude/skills/)
├── SKILL.md                       # 编排剧本(给 agent 的工作流)
├── scripts/
│   ├── codegen.py                 # IR → Python / TypeScript
│   ├── validate_ir.py             # IR schema 校验
│   └── coverage.py                # ① 用例覆盖 + ② UI 元素覆盖
├── reference/                     # ir-schema.md / locator-map.md(渐进披露)
└── ir/{schema.json, examples/}
tests/                             # 脚本单测(确定性保障)
```

## 快速试用

```bash
S=skills/foxtest
# 校验示例 IR
python $S/scripts/validate_ir.py $S/ir/examples/login.ir.json
# 生成双语言脚本
python $S/scripts/codegen.py $S/ir/examples/*.ir.json --lang both --out out/
# 跑脚本单测
pytest tests/
```

## 作为 Skill 启用(本地)

```bash
ln -s "$(pwd)/skills/foxtest" ~/.claude/skills/foxtest
```

## 作为 Claude Code Plugin 安装

### 方式 1: 直接克隆仓库

```bash
# 克隆仓库到本地 plugin 目录
git clone https://github.com/mofanx/foxtest ~/.claude/plugins/foxtest

# 或克隆到任意目录后创建 symlink
git clone https://github.com/mofanx/foxtest ~/foxtest
ln -s ~/foxtest ~/.claude/plugins/foxtest
```

### 方式 2: 手动安装

1. 克隆或下载本仓库
2. 确保 `.claude-plugin/plugin.json` 存在于仓库根目录
3. 将仓库放置在 Claude Code 的 plugins 目录中:
   - Linux/macOS: `~/.claude/plugins/`
   - Windows: `%USERPROFILE%\.claude\plugins\`

### 验证安装

启动 Claude Code 后，skill 应该自动被发现并可用。你可以通过以下方式验证:

```bash
# 检查 skill 文件是否存在
test -f ~/.claude/plugins/foxtest/skills/foxtest/SKILL.md && echo "安装成功"
```

### 依赖

本 plugin 依赖以下 skill:
- **dp-cli**: 浏览器感知与操作能力

请确保 dp-cli skill 也已正确安装。

## 路线

- [x] IR schema + 双语言 codegen
- [x] Skill 编排骨架 + IR 校验
- [x] ① 用例覆盖 + ② UI 元素覆盖
- [ ] M1:AI 探索循环(snapshot→决策→IR)实战打通
- [ ] ③ 前端 JS 代码覆盖(CDP / Playwright coverage)
- [ ] Claude Code plugin 正式发布(marketplace)


---

## 开发文档

详细的开发过程记录、设计决策和任务派单请查看 [docs/phase1-planning/](docs/phase1-planning/)。
