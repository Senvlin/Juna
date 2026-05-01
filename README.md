# Juna


---

## ✨ 功能概览

> 🚧 **早期开发阶段** — 已完成每日单词学习核心流程，更多功能持续开发中。

高中生一枚，手机上交班主任后只能用扇贝单词网页端学习，但发现网页端对全键盘支持并不友好，每次打卡都必须使用鼠标，于是通过分析api，自己实现了一个更适配键盘操作的单词学习工具QwQ

### 已实现

| 功能 | 状态 |
|------|------|
| 获取用户当前学习教材信息 | ✅ |
| 获取 **每日单词** 列表 | ✅ |
| **交互式拼写练习**（逐字母输入 + 自动检查） | ✅ |
| 查看其他用户的 **单词笔记** | ✅ |
| **导出** 单词数据为 JSON | ✅ |
| 全键盘操作支持 | ✅ |

### 计划中

- [ ] 导出单词数据为JSON
- [ ] 每日单词发送到Bot
- [ ] 单词同步回扇贝服务器
- [ ] 自定义学习计划
- [ ] 每日阅读爬取
---

## 快速开始

### 前置要求

- Python **3.11+**
- Node.js **18+** & pnpm

### 1. 配置 Cookie

复制 `backend/config.ini`，填入你的扇贝 Cookie：

```ini
[Cookie]
COOKIE="your_shanbay_cookie_here"
```

> 从浏览器登录 [扇贝网](https://www.shanbay.com) 后，通过开发者工具获取完整的 Cookie 字符串

### 2. 启动后端

```bash
# 激活虚拟环境（推荐）
# Windows
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动 API 服务（默认 http://127.0.0.1:8080）
uvicorn backend.src.main:app --host 127.0.0.1 --port 8080 --reload
```

### 3. 启动前端

```bash
cd frontend
pnpm install
pnpm dev
```

打开浏览器访问即可

---

## 致谢

- [扇贝网](https://www.shanbay.com) — 数据支持
- [yihong0618/shanbay_remember](https://github.com/yihong0618/shanbay_remember) — Python API 解码器参考实现

**仅供个人学习使用**