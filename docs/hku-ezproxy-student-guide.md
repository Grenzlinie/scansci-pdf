# HKU 学生：用 EZProxy 下载论文

这份指南帮助 HKU 图书馆用户在自己的电脑上，通过已获授权的 HKU EZProxy
访问订阅论文。完成后，你可以下载单篇 DOI，或批量下载 DOI 列表；登录 Cookie
只保存在你的本机。

请只下载 HKU 图书馆许可、出版商条款和当地法律允许你访问的内容。程序不会读取
你的密码，也不会自动绕过 CAPTCHA 或出版商验证。

## 1. 安装带浏览器支持的版本

本流程需要 `uv`。在终端运行以下命令，安装或替换为本仓库的最新版：

```bash
uv tool install --force \
  "scansci-pdf[cloakbrowser] @ git+https://github.com/Grenzlinie/scansci-pdf.git@master"
scansci-pdf browser-doctor
```

第二条命令应显示浏览器运行时状态；若提示缺少 CloakBrowser，请重新运行上面的
安装命令。该流程会启动独立的可见 Chromium，不复用你日常 Chrome 的 Profile。

## 2. 配置并登录 HKU EZProxy

先写入 HKU 的 EZProxy 登录模板：

```bash
scansci-pdf config-cmd ezproxy_enabled true
scansci-pdf config-cmd ezproxy_login_url 'https://eproxy.lib.hku.hk/login?url={url}'
```

然后启动登录：

```bash
scansci-pdf login --login-type ezproxy --manual-confirm
```

在打开的 Chromium 窗口中完成 HKU 图书馆登录。页面进入带
`.eproxy.lib.hku.hk` 的出版社地址后，回到终端按 Enter 保存 Cookie。终端显示
“登录状态已确认”或“登录成功”后即可关闭浏览器。

Cookie 默认保存在 `~/.scansci-pdf/cache/ezproxy_cookies.json`。不要把它发给他人、
上传到 GitHub、同步到公开网盘或提交到仓库。登录失效时，只需重新执行本节登录命令。

## 3. 下载一篇论文

将 DOI 替换为你的论文 DOI：

```bash
scansci-pdf get '10.1016/j.actamat.2026.122519' \
  --output ./papers --no-bibtex --ezproxy-only
```

`--ezproxy-only` 会跳过其他下载来源，直接使用已保存的 HKU EZProxy 登录态。成功时
终端会显示 `OK:` 和 PDF 路径；下载文件应出现在 `./papers`。

如果文章页或 PDF 页出现 `Processing Verification`、CAPTCHA 或类似页面，请保持
Chromium 窗口打开并手动完成验证。终端提示后，按 Enter 继续等待；输入 `skip` 才会
放弃当前论文。不要在终端仍在等待时关闭浏览器。

## 4. 批量下载：开放来源优先，EZProxy 兜底

创建一个文本文件，每行一个 DOI；空行和以 `#` 开头的说明行会被忽略：

```text
10.1016/j.actamat.2026.122519
10.1007/s00170-024-00000-0
# 这是说明行
```

运行：

```bash
scansci-pdf batch dois.txt --output ./papers --ezproxy --format json
```

`--ezproxy` 的每篇 DOI 按以下顺序处理：

1. 先尝试本地缓存及现有快速来源，包括 OpenAlex、Unpaywall、出版社开放 PDF 和其他
   已启用来源；此模式也会按你的要求启用 Sci-Hub 等灰色来源。
2. 第一阶段没有获得 PDF 时，才按顺序使用已登录的 HKU EZProxy。顺序执行可避免多个
   DOI 同时占用同一个浏览器登录会话。
3. 结果写入 `./papers/batch_results.json`，已成功项目可在下次运行中复用进度。

Sci-Hub 不是开放获取来源；是否使用它由你自行判断，并须遵守适用条款和法律。若只想
使用 HKU 订阅，请改用第 3 节的单篇 `--ezproxy-only` 命令。

## 5. 常见情况

| 情况 | 处理方式 |
|---|---|
| 登录后仍显示登录页 | 重新运行登录命令；确认地址栏已变为带 `.eproxy.lib.hku.hk` 的出版社地址后再按 Enter。 |
| Cookie 过期 | 重新执行第 2 节。不要手动编辑 Cookie 文件。 |
| 看到验证页 | 在可见浏览器手动完成验证，回终端按 Enter 继续等待。 |
| `EZProxy is not configured` | 重新执行第 2 节前两条配置命令。 |
| 批量中某篇失败 | 查看 `batch_results.json`；确认 HKU 是否订阅该期刊，再针对该 DOI 重试。 |
| 不再使用本机登录态 | 删除 `~/.scansci-pdf/cache/ezproxy_cookies.json`，下次使用时重新登录。 |

## 完成标准

你已完成配置，当以下三项同时成立：

- 登录命令保存了本机 Cookie；
- 单篇命令输出 `OK:` 且目标目录中有可打开的 PDF；
- 批量命令生成 `batch_results.json`，其中每篇论文都有成功或失败记录。
