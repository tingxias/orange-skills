# Project Notes

## Known Project Roots

- `mitejia`: `/Users/a1234/Documents/work/yonyou/project/mitejia/mitejia`
- `yingke-zs`: `/Users/a1234/Documents/work/yonyou/project/yingke-zs/yingke-zs`
- `yingke-old`: `/Users/a1234/Documents/work/yonyou/project/yingke-zs/yingke-old`
- `qicheng`: `/Users/a1234/Documents/work/yonyou/project/qicheng/qicheng`
- `qicheng-sync`: `/Users/a1234/Documents/work/yonyou/project/qicheng/sync`

## Mitejia Layout

- IC public API processors: `ic/src/public/nc/buss/ic/processor`
- IC private action overrides: `ic/src/private/nc/bs/pub/action`
- PU private action overrides: `pu/src/private/nc/bs/pub/action`
- SO private action overrides: `so/src/private/nc/bs/pub/action`
- MES shared services/models: `uapbd/src/public/nc/buss/mes/push`
- Batch helper: `uapbd/src/public/com/yonyou/sync/util/BatchCodeUpdateUtil.java`

## Current Conventions

- Public APIs usually extend `AbstractApiProcessor`.
- Private NC actions usually extend `AbstractCompiler2`.
- Shared database access often uses `SyncQueryDataUtil`.
- Data dictionary/custom archive access usually uses the local project's `SyncQueryDataUtil`, `QueryDataUtil`, or existing `PubQueryService`; do not introduce a new lookup helper unless the module already has that pattern.
- New API body params live under each processor package's `model` directory.
- For generated or decompiled NC action classes, match existing style and avoid broad refactors.

## Yingke-ZS / Yingke-Old Patterns

- `yingke-zs` has a `uapbd`-centered OpenAPI framework.
- `yingke-old` includes modules such as `pu`, `erm`, `uapbd`, `hrhi`.
- Common base classes:
  - `nc.custom.pub.openapi.process.OpenApiDataBussProcess`
  - `nc.custom.pub.openapi.process.bill.BillBussProcess`
- Common servlet path style:
  - `*/src/public/nc/buss/openapi/**`
  - rule processors often live under `rule/actuator`.

## Qicheng Patterns

- `qicheng/qicheng` uses the OpenAPI/rule framework similar to `yingke-old`.
- `qicheng/sync` uses a sync dispatcher and `AbstractApiProcessor` pattern similar to `mitejia`.
- Important qicheng paths:
  - `qicheng/qicheng/uapbd/src/public/nc/custom/pub/openapi`
  - `qicheng/qicheng/*/src/public/nc/buss/openapi`
  - `qicheng/sync/uapbd/src/public/com/yonyou/sync/servlet/processor`
  - `qicheng/sync/ic/src/public/nc/buss/ic/processor`
  - `qicheng/sync/uapbd/resources/processors.list`

## Sync Framework Paths

- Dispatcher: `uapbd/src/public/com/yonyou/sync/servlet/servlet/CoreApiDispatcherServlet.java`
- Processor base: `uapbd/src/public/com/yonyou/sync/servlet/processor/AbstractApiProcessor.java`
- Processor factory/registry: `uapbd/src/public/com/yonyou/sync/servlet/factory`
- Response model: `uapbd/src/public/com/yonyou/sync/servlet/core/ApiResult.java`
- Push services: `uapbd/src/public/com/yonyou/sync/service`
- Query utilities: `uapbd/src/public/com/yonyou/common/util/SyncQueryDataUtil.java` or `uapbd/src/public/com/yonyou/sync/util/SyncQueryDataUtil.java`

## Choosing The Pattern

- If the project has `com.yonyou.sync.servlet.processor.AbstractApiProcessor`, follow the sync processor template.
- If the project has `OpenApiDataBussProcess`/`BillBussProcess`, follow the OpenAPI rule template.
- If editing private NC action overrides, follow the `AbstractCompiler2` action template.
