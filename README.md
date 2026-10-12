# 亿万僵尸中文修订 / They Are Billions Chinese Patch

面向 **Steam 1.0.14（64位）** 的非官方简体中文修订。改善生硬或误导性的译文，统一术语，并修正已发现的中文排版问题。

目前在 Linux / Proton Experimental 环境验证。只支持与项目基准哈希匹配的资源；其他平台、版本或不同资源构建尚未验证。

## 覆盖内容

| 资源 | 修订范围 |
| --- | --- |
| 主翻译表 `ZXStrings.dat` | 累计753个中文单元格，涉及界面、科技、单位与建筑说明、帮助、提示和更新说明 |
| 官方战役 `ZXCampaignStrings.dat` | 同步479条记录，311个中文单元格变化；覆盖任务、教程、英雄说明、字幕与新闻档案 |
| [官方50日挑战](https://steamcommunity.com/sharedfiles/filedetails/?id=1559552741) | 12条文本中修订9条，并调整介绍页的断行 |

不同资源之间包含重复译文，上述数量不能直接相加为独立翻译条数。项目不改游戏数值或存档，也不修改玩家自制地图、模组的文本文件。

## 快速开始

仓库发布修订数据和工具，不包含游戏原始资源或完整游戏文件。请使用自己安装的匹配版本游戏构建补丁。

需要：Python **3.10+**、PATH中的 **`7z`**，以及已下载的官方50日挑战（Workshop ID `1559552741`）。Python仅使用标准库。

```sh
git clone https://github.com/pai535Huang/they-are-billions-chinese-patch.git
cd they-are-billions-chinese-patch

# 将匹配的原版文本资源复制到项目的 originals/，不改游戏安装
python3 scripts/prepare.py

# 构建并检查安装/恢复流程，测试只使用临时副本
python3 scripts/build.py
python3 scripts/verify_install.py

# 完全退出游戏后安装
python3 releases/v0.3/manage_patch.py install
```

Steam位于其他目录时，准备和安装都需指定游戏目录：

```sh
python3 scripts/prepare.py --game-dir '/实际路径/steamapps/common/They Are Billions'
python3 releases/v0.3/manage_patch.py install --game-dir '/实际路径/steamapps/common/They Are Billions'
```

已安装过本项目补丁时，可用此前补丁包的原版备份准备构建输入：

```sh
python3 scripts/prepare.py --backup-dir '/原版备份所在目录'
```

`prepare.py`会先校验三份资源，再复制到本地项目。版本号相同但资源哈希不同，也会停止，不会把已修改的资源当作原版备份。

## 恢复原版

完全退出游戏后执行：

```sh
python3 releases/v0.3/manage_patch.py restore
```

恢复也支持`--game-dir`。安装工具在写入前校验所有目标和备份；任何文件不匹配都停止。写入失败时会回退已经写入的文件。Steam更新或文件验证可能覆盖修订，届时应重新检查兼容性。

## 排版与验证

在3072×1920画面下实机检查了主菜单、官方50日挑战介绍和两位英雄说明。已修复这些页面中的标点孤行、名称拆分和转义字符显示问题。

这不是全量重译，也不代表所有关卡、悬浮提示、字幕及其他分辨率均已检查。[验证范围与修改前后截图](docs/排版验证.md)记录了实际检查结果。重新构建会保留该记录，但新的译文改动仍需要重新进行游戏内验证。

## 参与修订

编辑以下文件后，重新构建、运行校验并在游戏中复查：

- `translations/text.json`：按表名、记录ID组织的中文文本。
- `translations/names.json`：单位和建筑名称。
- `translations/glossary.json`：统一术语的替换规则。

请保留`{0}`等占位符、现有记录ID和标记。主表、独立战役与官方关卡CSV的换行处理不同；CSV介绍页不解释字面的`\n`。提交问题时，请提供游戏版本、界面位置、显示分辨率以及有问题的文字或截图。

构建会检查XML、记录与列定义、非中文单元格、占位符以及压缩包解压往返。安装校验使用临时目录，不操作真实Steam安装。

```sh
python3 -m unittest discover -s tests
```

## 项目结构

```text
translations/   中文修订数据
scripts/        原版资源准备、构建及校验工具
templates/      安装工具与补丁说明模板
docs/           排版报告、截图及结构审计
config.json     支持版本、基准哈希与资源归档参数
originals/      使用者本地提供的原版资源（Git忽略）
build/          构建中间文件（Git忽略）
releases/       本地生成的补丁与备份（Git忽略）
```

## 许可与致谢

本项目自行编写的代码和修订数据采用[MIT许可证](LICENSE)。原游戏及其资源的权利属于原权利人；它们不随本仓库发布。项目与Numantian Games没有官方关联。

归档格式研究参考了[TABCrypt](https://github.com/GabKeinenAnderenNamenMehr/TABCrypt)，官方50日挑战由Numantian Games制作。
