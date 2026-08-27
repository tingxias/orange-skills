---
name: yonyou-skill
description: NC65接口开发与维护经验，适用于 mitejia、yingke-zs、qicheng 等用友NC项目。Use when implementing or reviewing NC65 bill APIs, NC65 data dictionary and primary-key/code lookups, bd_defdoc/bd_defdoclist custom archives, sync dispatcher/AbstractApiProcessor/processors.list work, AbstractCompiler2 actions, OpenAPI rule processors, PfServiceScmUtil bill conversion, SyncQueryDataUtil queries, sync push/writeback services, MES push/check services, inventory pre-checks, batch-code updates, free fields, custom fields, material-class push rules, and save/approve/delete flows.
---

# NC65 API Dev

Use this skill for NC65 bill APIs, sync processors, OpenAPI/rule servlets, MES push/check services, batch-code updates, and related bill-body mapping work.

## Scope

- NC65/NC接口新增、修改、删除、审核、弃审、保存前校验
- `AbstractApiProcessor`、`OpenApiDataBussProcess`、`BillBussProcess`、`AbstractCompiler2` 相关开发
- `PfServiceScmUtil`、`SyncQueryDataUtil`、`QueryDataUtil`、`IPFBusiAction.processBatch` 相关开发
- MES调用、MES现存量校验、推送规则、返回码判定
- 表头/表体字段映射、批次字段、自定义项、自由项、物料分类规则
- NC65数据字典、基础档案、自定义档案、编码与主键互转

## Workflow

1. Read the target module first. Prefer existing local patterns over new abstractions.
2. Identify which framework the project uses: sync `AbstractApiProcessor`, OpenAPI/rule `OpenApiDataBussProcess`/`BillBussProcess`, or private `AbstractCompiler2` action.
3. Identify whether each incoming/outgoing field expects an NC primary key, code, name, or custom archive value.
4. Identify bill type, action, body VO, batch VO, and save/approve entrypoint.
5. Use `codegraph_explore` for flow and symbol discovery when the project has `.codegraph/`.
6. For sync framework work, verify dispatcher registration, `processors.list`, `ApiProcessor` code, and package differences before copying imports.
7. For MES integration, reuse the shared push/check service and adapt request shaping in the service layer.
8. Keep body field extraction local to the processor unless a stable shared helper already exists.
9. If batch custom fields are involved, preserve unrelated batch fields. Update only the requested keys.
10. Validate by checking the exact save path, body row generation, post-save hooks, and batch update flow.

## Working Rules

- Keep edits aligned with existing project style, even when that means small duplicated mapping blocks.
- Treat one-to-many source/target row mapping carefully. Do not reuse the same body VO object when one source row can split into multiple target rows.
- Use `LinkedHashMap` when request row order must be preserved across grouping.
- When a request or response format changes, update both the service wrapper and the request/response model.
- When adding comments, explain business intent, not obvious assignments.

## References

- [Project notes](references/projects.md)
- [Sync framework](references/sync-framework.md)
- [NC65 data dictionary](references/data-dictionary.md)
- [NC bill patterns](references/nc-patterns.md)
- [MES integration patterns](references/mes-patterns.md)
