Table of Contents
=================

   * [Mailman RESTful](#mailman-restful)
      * [mailmancli](#mailmancli)
      * [mailman RESTful API](#mailman-restful-api)
         * [公共信息](#公共信息)
         * [返回信息](#返回信息)
         * [API](#api)
      * [mailman RESTful server](#mailman-restful-server)

Created by [gh-md-toc](https://github.com/ekalinin/github-markdown-toc)

# Mailman RESTful

Mailman2.1 版本并没有开放 API，对此开发了 RESTful service 已增强 Mailman 管理功能。项目提供 RESTful server 和 CLI 接口可执行程序。

在 Mailman 服务器上部署运行 RESTful server，向外提供 RESTful API。用户可以直接使用用 CLI 程序，以访问 RESTful URL 形式管理邮件列表。

## mailmancli
---

mailmancli 是一个命令行工具。malimancli 接收命令行参数，发送 RESTful 请求到 mailmanrest server，然后打印 Server 信息到标准输出中。

基本用法：

```
$ mailmancli action [options] [mails,] listname
    action：
        add: 添加 [-f file] 和 mails 指定的所有邮件到邮件组 <listname>。
        remove: 删除 [-f file] 和 mails 指定的所有的邮件。
        show-pending: 显示 <listname> 上所有等待 approval 的邮件地址。
        approve: 接受 [-f file] 和 mails 中所有等待 approval 的邮件地址。
    [options]:
        -f file: 指定一个包含邮件地址列表的文件，每行一个邮件地址。
        -h: 帮助信息
    listname: 需要管理的邮件组
```

mailmancli 有两个可配置的环境变量。

```
export MAILMAN_SERVER=127.0.0.1
export MAILMAN_LIST_PASSWD=YOUR_PASSWORD
```

其中 MAILMAN_SERVER 为 mailman 服务器名，一般情况用户不需要更改。

MAILMAN_LIST_PASSWD 需要用户配置成邮件组的管理密码或者审核人密码。

注意 mailman 会检查邮件地址合法性。用户只可以添加和管理 \*@qiyi.com 的地址。

## mailman RESTful API
---

### 公共信息
---

1. RESTful API 默认使用 5000 端口
2. 公共返回参数包括 code/message，分别用于表示 API 执行状态和对状态的描述

### 返回信息
---

| http code     | 描述     |
| -------------:|---------:|
| 200           |请求成功   |
| 400           |请求类型错误|
| 500           |程序内部错误|

### API
---

- 添加用户

    添加一个或多个用户到邮件组。

    - **URL:**

        /api/add

    - **Method:**

        `POST`

    - **URL Params:**

        None

    - **Data Params:**

        `passwd=[string]`

        `listname=[string]`

        `member=[array]`

    - **例子：**

        ```
        $ curl http://localhost:5000/add -H "Content-Type: application/json" -i -d \
        '{"passwd":"changeme","listname":"test", "members":["test@qiyi.com]}' -X POST
        ```

- 移除用户

    移除一个或多个用户到邮件组

    - **URL:**

        /api/remove

    - **Method:**

        `POST`

    - **URL Params:**

        None

    - **Data Params:**

        `passwd=[string]`

        `listname=[string]`

        `member=[array]`

    - **例子：**

        ```
        $ curl http://localhost:5000/remove -H "Content-Type: application/json" -i -d \
        '{"passwd":"changeme","listname":"test", "members":["test@qiyi.com]}' -X POST
        ```

- 列出等待审批用户

    - **URL:**

        /api/pending

    - **Method:**

        `GET`

    - **URL Params:**

        `passwd=[String]`

        `listname=[String]`

    - **Data Params:**

        None

    - **例子：**

        ```
        $ curl http://localhost:5000/api/pending  -i -d "passwd=changeme" -d "listname=test" -X GET
        ```

- 同意用户请求

    通过用户的加入请求。注意该 API 只接受已经提交申请的用户。对于未提交申请的用户，请使用 api/add 直接添加。

    - **URL:**

        /api/approve

    - **Method:**

        `POST`

    - **URL Params:**

        None

    - **Data Params:**

        `passwd=[String]`

        `listname=[String]`

    - **例子：**

        ```
        $ curl http://localhost:5000/approve -H "Content-Type: application/json" -i -d \
        '{"passwd":"changeme", "listname":"test"}' -X POST
        ```

## mailman RESTful server
---

mailman RESTful server 是一个基于 Flask 的 RESTful server。默认使用 5000 端口。以 root 权限运行 start.sh 脚本启动 server。服务日志会默认放在 `/var/log/mailman/rest.server.log` 中。

无任何参数，mailman RESTful server 运行在普通模式。

```
# $(MAILMAN_RESTful_HOME)/start.sh
```

对于开发人员，可以使用选项 '-t' 运行在测试模式。

```
# $(MAILMAN_RESTful_HOME)/start.sh -t
```
