# F7 派单:Claude Code plugin 正式化(交给执行 AI)

> 目标:把 foxtest 仓库完善为可分发的 Claude Code plugin。
> `$ROOT` = foxtest 仓库根,`$S = $ROOT/skills/foxtest`。

## 前置依赖
- **F1–F4 基本成型**(plugin 内容值得分发)。无强制硬依赖,但建议在核心能力可用后做。
- 预检:`test -f $ROOT/.claude-plugin/plugin.json && test -f $S/SKILL.md && echo "基础就绪"`

## 重要:先查官方规范
Claude Code plugin / Agent Skills 的清单字段与目录约定**以官方文档为准**。动手前先查证:
- plugin.json 的合法字段、components 声明方式;
- marketplace.json 的结构;
- skill 在 plugin 中的发现路径(应保持 `skills/foxtest/`)。
**不确定的字段不要臆造**,查到再写。

## 范围
1. 完善 `$ROOT/.claude-plugin/plugin.json`:补全 name/version/description/author/keywords 之外的 **components 声明**(指向 `skills/`、未来的 `commands/`)。
2. (可选)新增斜杠命令 `commands/foxtest-gen.md`(如 `/foxtest-gen <用例文件>`),内部走 SKILL 工作流。
3. 新增 `marketplace.json`(或 `.claude-plugin/marketplace.json`),把 foxtest 列为可安装 plugin。
4. README 增补「作为 plugin 安装/启用」章节(命令可复制执行)。

## 约束
- 不破坏 skill 的独立 symlink 能力(`ln -s $S ~/.claude/skills/foxtest` 仍须可用)。
- 不改动 skill 内部脚本逻辑(本单只做打包/分发层)。

## DoD 验收
```bash
python -c "import json; json.load(open('$ROOT/.claude-plugin/plugin.json')); print('plugin.json 合法')"
test -f $ROOT/.claude-plugin/marketplace.json || test -f $ROOT/marketplace.json && echo "marketplace 存在"
test -f $S/SKILL.md && echo "skill 可被发现"
# 若加了斜杠命令
test -f $ROOT/commands/foxtest-gen.md && echo "命令存在(可选)"
```
**通过标准:**
- [ ] plugin.json 合法,且按官方规范声明了 skill component
- [ ] marketplace 条目存在且字段符合官方规范
- [ ] README 安装/启用章节命令可复制执行
- [ ] skill 仍可单独 symlink 生效

## 禁止事项
- 不臆造未在官方文档中确认的 plugin/marketplace 字段。
- 不把脚本逻辑改动混入本单。

## 交付物
1. `$ROOT/.claude-plugin/plugin.json`(完善)
2. marketplace 文件
3. (可选)`commands/foxtest-gen.md`
4. README 安装章节;DoD 输出 + 勾选 + 引用的官方文档链接
