# High-Level Architecture (stub)
```mermaid
graph TD
  EXT[Browser Extension] --> API
  UI[Dashboard] --> API
  API --> PG[(Postgres)]
  API --> WMK[Watermark Service]
```
