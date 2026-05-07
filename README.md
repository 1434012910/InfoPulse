# InfoPulse - 资讯采集框架

一个高扩展性、配置化、具备反爬能力的Python资讯采集框架。

## 功能特性

### 采集能力
- 支持App端采集（接口逆向、直连）
- 支持Web端采集（接口逆向、静态XPath解析、CSS选择器）
- 支持增量采集，只抓取新增或更新的内容
- 采集频率和间隔时间配置化

### 反爬机制
- 请求频率控制
- 代理IP支持（预留接口）
- Cookie管理与登录态维持
- User-Agent随机切换

### 逆向代码管理
- 逆向逻辑以独立的.js文件存储
- 框架动态加载并执行JS逆向逻辑
- 逆向失效时记录日志并告警

### 解析规则配置化
- XPath解析规则写入JSON配置文件
- 支持CSS选择器作为备选解析方式
- 可配置字段：标题、正文、发布时间、作者、来源、图片链接等

### 数据处理
- Redis去重：基于URL或内容指纹的布隆过滤器
- SQLite存储：持久化存储采集数据
- 日志系统：完整记录采集过程、错误信息、性能指标

### 容错与可靠性
- 错误重试机制：支持配置重试次数和重试间隔
- 单个采集源失败不影响其他采集源
- 监控告警：连续失败、采集异常或逆向失效时触发告警

### Web管理界面
- 查看采集任务运行状态
- 手动触发或暂停采集任务
- 查看采集日志
- 采集源配置的可视化管理

## 技术栈

- Python 3.8+
- Redis：URL/内容指纹去重
- SQLite：资讯数据持久化存储
- Flask：Web管理界面
- APScheduler：任务调度
- lxml：HTML/XML解析
- PyExecJS：JavaScript执行

## 安装

1. 克隆项目
```bash
git clone https://github.com/1434012910/InfoPulse.git
cd InfoPulse
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置Redis（可选，不配置则使用本地布隆过滤器）
```bash
# 修改 config/config.json 中的Redis配置
```

## 使用方法

### 启动全部服务
```bash
python run.py --mode all
```

### 仅启动调度器
```bash
python run.py --mode scheduler
```

### 仅启动Web管理界面
```bash
python run.py --mode web --port 5000
```

### 自定义配置
```bash
python run.py --config /path/to/config.json --sources /path/to/sources.json
```

## 配置说明

### 主配置文件 (config/config.json)
- Redis连接配置
- SQLite数据库路径
- 日志配置
- 告警配置
- 采集器全局参数
- 代理配置
- Web管理界面配置

### 采集源配置文件 (config/sources.json)
每个采集源包含：
- name：采集源名称
- enabled：是否启用
- type：类型（app/web）
- method：采集方式（reverse/direct/static）
- url：请求地址
- js_file：逆向JS文件路径（如适用）
- interval：采集间隔（秒）
- retry_times：重试次数
- timeout：超时时间
- incremental：是否增量采集
- headers：请求头
- cookies：Cookie配置
- parse_config：解析规则配置

## 添加新采集源

1. 在 `js_reverse/` 目录下创建JS逆向文件（如需要）
2. 在 `config/sources.json` 中添加采集源配置
3. 重启服务或通过Web管理界面重新加载配置

## 目录结构

```
InfoPulse/
├── config/                 # 配置文件
│   ├── config.json        # 主配置
│   └── sources.json       # 采集源配置
├── core/                   # 核心模块
│   ├── config.py          # 配置管理
│   ├── logger.py          # 日志管理
│   ├── redis_client.py    # Redis客户端
│   └── sqlite_client.py   # SQLite客户端
├── collectors/             # 采集器
│   ├── base_collector.py  # 采集器基类
│   ├── collector_factory.py # 采集器工厂
│   ├── app_*.py           # App端采集器
│   └── web_*.py           # Web端采集器
├── parsers/                # 解析器
├── dedup/                  # 去重模块
├── storage/                # 存储模块
├── anti_crawl/             # 反爬模块
├── js_reverse/             # JS逆向文件
├── scheduler/              # 调度器
├── web_admin/              # Web管理界面
├── templates/              # HTML模板
├── data/                   # 数据目录
├── logs/                   # 日志目录
├── run.py                  # 启动脚本
└── requirements.txt        # 依赖列表
```

## Web管理界面

启动后访问 http://localhost:5000

功能包括：
- 仪表盘：查看系统概览和统计数据
- 任务管理：查看、暂停、恢复、手动触发采集任务
- 采集源管理：添加、编辑、删除采集源配置
- 采集日志：查看采集历史日志
- 采集数据：查看采集到的资讯数据

## 分布式扩展

当前版本为单机运行，未来可扩展为分布式：
- Redis可作为分布式去重中心
- Redis可作为任务队列
- 支持多节点部署

## 许可证

MIT License