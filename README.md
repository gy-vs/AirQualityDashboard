# 城市空气质量监控仪表盘

基于 FastAPI + ECharts + SQLite 的城市空气质量监控仪表盘 Web 应用，支持全国 30 个主要城市 AQI 实时监控、地图热力图、污染预警及历史数据查询。

---

## How to Run

```bash
docker compose up --build -d
```

## Services

| 服务 | 端口 | 说明 |
|------|------|------|
| Web App | 8080 | 仪表盘前端 + API |

访问地址：http://localhost:8080

## 技术栈

- **后端**: Python 3.11 + FastAPI + SQLAlchemy
- **前端**: Jinja2 模板 + ECharts
- **数据库**: SQLite
- **容器化**: Docker + Docker Compose
