# Python版本说明

## ⚠️ 重要提示

**本项目必须使用 Python 3.11 版本！**

项目所有代码和依赖都在 Python 3.11 环境下开发和测试，确保稳定性和兼容性。

## 🔍 为什么使用Python 3.11？

1. **稳定性**: Python 3.11 是经过充分测试的稳定版本
2. **依赖兼容**: 所有依赖包都有Python 3.11的预编译wheel文件
3. **PyCharm配置**: 开发环境基于Python 3.11
4. **避免问题**: Python 3.14太新，很多包还没有完全支持，会导致编译错误

## 📥 如何安装Python 3.11

### Windows用户

1. **下载Python 3.11.9**
   - 访问: https://www.python.org/downloads/release/python-3119/
   - 选择: `Windows installer (64-bit)`

2. **安装时设置**
   - ✅ 勾选 "Add Python 3.11 to PATH"
   - ✅ 勾选 "Install for all users"（可选）
   - 点击 "Install Now"

3. **验证安装**
   ```cmd
   python --version
   # 应该显示: Python 3.11.9

   # 或者
   py -3.11 --version
   ```

### Linux用户

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# 验证
python3.11 --version
```

### Mac用户

```bash
# 使用Homebrew
brew install python@3.11

# 验证
python3.11 --version
```

## 🔧 如果已经安装了其他Python版本

### 多版本共存（推荐）

Python支持多个版本同时安装，使用`py`启动器选择版本：

```cmd
# Windows
py -3.11 --version     # 使用Python 3.11
py -3.14 --version     # 使用Python 3.14（如果已安装）

# Linux/Mac
python3.11 --version
python3.14 --version
```

### 创建虚拟环境时指定版本

```cmd
# Windows
py -3.11 -m venv venv

# Linux/Mac
python3.11 -m venv venv
```

## ✅ 验证Python版本

创建虚拟环境后，验证使用的是Python 3.11：

```cmd
# 激活虚拟环境
venv\Scripts\activate    # Windows
source venv/bin/activate # Linux/Mac

# 检查版本
python --version
# 必须显示: Python 3.11.x

# 检查具体路径
python -c "import sys; print(sys.executable)"
```

## 🚫 如果使用了错误的Python版本

如果不小心使用Python 3.14创建了虚拟环境：

```cmd
# 1. 删除错误的虚拟环境
rmdir /s /q venv    # Windows
rm -rf venv         # Linux/Mac

# 2. 使用Python 3.11重新创建
py -3.11 -m venv venv           # Windows
python3.11 -m venv venv         # Linux/Mac

# 3. 激活并验证
venv\Scripts\activate           # Windows
python --version                # 确认是3.11.x
```

## 📋 依赖兼容性

| 依赖包 | Python 3.11 | Python 3.14 |
|--------|-------------|-------------|
| FastAPI | ✅ 完美 | ✅ 兼容 |
| Pydantic | ✅ 完美 | ⚠️ 需要编译 |
| PyAudio | ✅ 完美 | ❌ 编译困难 |
| SQLAlchemy | ✅ 完美 | ✅ 兼容 |

## 🎯 推荐配置

**最佳实践:**
- ✅ 使用 Python 3.11.9
- ✅ 在虚拟环境中安装依赖
- ✅ 使用 `requirements.txt`（不是 requirements-py314.txt）

**PyCharm配置:**
1. File → Settings → Project → Python Interpreter
2. 点击 ⚙️ → Add...
3. 选择 Virtualenv Environment
4. Base interpreter 选择 Python 3.11

## ❓ 常见问题

**Q: 我已经安装了Python 3.14，必须卸载吗？**
A: 不需要。可以保留多个Python版本，使用 `py -3.11` 来指定使用3.11。

**Q: requirements-py314.txt是什么？**
A: 那是为Python 3.14准备的临时文件，您不需要使用它。请使用 `requirements.txt`。

**Q: 安装依赖时出现编译错误怎么办？**
A: 确保使用Python 3.11。如果确认是3.11还有问题，请查看 INSTALL.md 的故障排除部分。

## 📞 获取帮助

如果在Python版本问题上遇到困难：
1. 查看 [INSTALL.md](INSTALL.md) 的详细安装指南
2. 查看 [QUICK_TEST.md](QUICK_TEST.md) 的测试步骤
3. 确认使用 `python --version` 显示的是 3.11.x

---

**记住: 本项目使用 Python 3.11！** 🐍✨
