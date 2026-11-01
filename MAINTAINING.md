# 维护说明

这个仓库是 GitBook 站点 `syz-notes` 的唯一内容来源。**所有改动都在这里完成，永远不要在 GitBook 网页上编辑**——Git Sync 是双向的，两边同时改会产生冲突和重复文件。

## 两个必须同步更新的文件

| 文件 | 作用 | 漏了会怎样 |
|---|---|---|
| `notes/SUMMARY.md` | 左侧导航树，同时决定 GitBook 收录哪些页面 | **页面不会被导入**，且不报错 |
| `notes/README.md` | 站点首页的课程总览 | 首页列表缺少这门课 |

新增一门课程或一个课时，**这两个文件都要改**。

## 目录结构

```
notes/
├── README.md                      站点首页（课程总览）
├── SUMMARY.md                     导航树
└── ke-cheng-ji-lu/
    └── <course-slug>/            一门课程
        ├── README.md             课程首页（课时列表）
        ├── <lesson-slug>/        一节课
        │   ├── README.md         正文
        │   └── images/           这节课自己的图片
        └── <lesson-slug>/
```

每节课是**独立目录**，图片放在该目录的 `images/` 下，正文用相对路径引用：

```markdown
![说明](images/f001.jpg)
```

不要把所有图片集中到某个公共目录——那样同名文件会互相覆盖。

## 新增一节课

```bash
cd ~/code/syz-notes
git pull

mkdir -p notes/ke-cheng-ji-lu/<course-slug>/<lesson-slug>/images
# 放入 README.md 和 images/

# 1) SUMMARY.md 里在对应课程下加一行（缩进两格）：
#   * [课时标题](ke-cheng-ji-lu/<course>/<lesson>/README.md)

# 2) 如果新增的是整门课程，还要在 README.md 对应分组下加一行

git add -A
git commit -m "add: <课时标题>"
git push
```

## 新增一门课程

1. 建目录 `notes/ke-cheng-ji-lu/<course-slug>/`，放课程 `README.md`（课时列表）
2. 课时照上面的结构逐个建立
3. `SUMMARY.md`：在「嵌入式与机器人」/「大模型与 AI 应用」/「工程与运维实践」三个分组里选一个，加课程名和课时行
4. `README.md`：在同一个分组下加一行课程简介

## 从 Obsidian 搬内容

源知识库在 `~/code/obsidian_本地知识库/笔记记录/`。搬的时候：

- **只搬** `note.md` 和 `images/`
- **不搬** `sources/`（字幕、ASR）、`*.html`、`render.json`、`validation.json`、`course-progress.json` 等制作产物
- 图片路径**不需要改写**——源文件本来就用 `images/f001.jpg` 相对路径，结构对齐后直接生效

## 注意事项

- 编辑前一定 `git pull`：GitBook 可能已经写回了一些提交
- 文件名避免空格和全角符号；图片用 `f001.jpg` 这类命名
- 页面 URL 由文件路径决定，`README.md` 会被省略：`<course>/<lesson>/README.md` → `/<course>/<lesson>`
- 改动后等几十秒，GitBook 才会同步完成
