# Sync Framework

Use this reference for `mitejia` and `qicheng/sync` projects that expose NC APIs through the `com.yonyou.sync` dispatcher and `AbstractApiProcessor` template.

## Entry Flow

Typical servlet entry:

- `com.yonyou.sync.servlet.servlet.CoreApiDispatcherServlet`
- Implements NC `IHttpServletAdaptor`.
- `doAction` initializes `ComponentManager`, then delegates to `process`.
- `process` builds `RequestContext`, runs the handler chain, writes `ApiResult` as JSON, logs success/error, and releases `PKLock` dynamic locks in `finally`.

Do not bypass this entry for normal API work. New APIs should usually add or register a processor, not add a second servlet.

## Request Context

Common fields:

- `requestId`, `traceId`
- `apiCode`, `apiName`
- `requestData`
- `clientIp`, `userAgent`, `requestMethod`, `requestUrl`, `requestHeaders`
- `result`, `startTime`, `endTime`

Package differences matter:

- `mitejia`: often uses `com.yonyou.sync.servlet.model.RequestContext`, `BillBodyItem`, `CommonBillResult`, and `com.yonyou.sync.repository.CusSyncDBService`.
- `qicheng/sync`: some classes use `com.yonyou.common.domain.model.RequestContext`, `BillBodyItem`, `CommonBillResult`, and `com.yonyou.common.repository.CusSyncDBService`.

Check the target project's imports before copying code between projects.

## Processor Registration

Registration usually flows through:

- `ApiProcessorFactory`
- `ApiProcessorRegistry`
- `ApiProcessorConfigFileRegistry`
- `ApiProcessorManualRegistry`
- `uapbd/resources/processors.list`

Preferred registration is `processors.list`: one fully qualified processor class name per line. Empty lines and `#` comments are ignored. Missing classes are skipped so the same list can be reused across different projects.

When adding a processor:

1. Implement `ApiProcessor` through `AbstractApiProcessor` unless the project has a more specific local base class.
2. Return the exact interface code from `getSupportedApiCodes`.
3. Add the full class name to `uapbd/resources/processors.list` when config registration is active.
4. Keep manual registration only for old compatibility or when the project already uses it for the target module.

## AbstractApiProcessor Template

`AbstractApiProcessor.process(RequestContext)` is final in the common framework. Subclasses implement the template steps:

1. `convertRequestData(String requestBody)`: parse JSON into a request model.
2. `validateBusinessParams(Object requestData)`: validate required fields and business state.
3. `executeBusinessLogic(Object requestData)`: build, convert, save, approve, write back, or call another system.
4. `buildSuccessResult(Object businessResult)`: customize response data if needed.

Common helper:

- `saveAggregatedVO(aggregatedVO, actionType, billTypeCode)` saves through `CusSyncDBService.saveAggVO_RequiresNew`.

Keep request parsing, validation, business execution, and result construction separate. This makes it easier to find the exact failed phase in logs.

## Result Format

`ApiResult` carries:

- `success`
- `code`
- `message`
- `data`
- `traceId`

Use `ApiResult.success("处理成功", data)` for normal success. Use `ApiResult.failure(ApiResponseCode, message)` or throw business exceptions when the framework's error handler should build the final response.

## Bill API Pattern

For IC/PU/SO bill processors under paths such as:

- `ic/src/public/nc/buss/ic/processor`
- `pu/src/public/nc/buss/pu/processor`
- `uapbd/src/public/nc/buss/**/processor`

Typical responsibilities:

- Request model lives under the processor package's `model` directory.
- `convertRequestData` uses the project's JSON utility pattern.
- `validateBusinessParams` checks header fields, body list, source bill relation, and required NC primary keys.
- `executeBusinessLogic` converts source bills or builds aggregate VOs.
- Save uses `saveAggregatedVO(vo, "WRITE", billTypeCode)` or the local action helper.
- `buildSuccessResult` returns NC bill id, bill no, source/third bill no, and body row ids when the local processor convention does so.

## Sync Push Service Pattern

The sync service layer is broader than MES. Common base classes include:

- `AbstractBillSyncPushService`: global sync key and generic log persistence.
- `AbstractSingleBillSyncPushService`: single-bill logging and source/target bill pk/code extraction.
- `ERP2HttpBillSyncPushService`: ERP to HTTP four-step flow.
- `MesBillSyncPushService`: MES-specific HTTP sending and response parsing.
- `SingleNC2NCBillSyncPushService`: NC to NC single-bill sync with default vdef writeback support.

`ERP2HttpBillSyncPushService` flow:

1. `convertToHttpFormat(sourceData)`
2. `sendHttpRequest(convertedData)`
3. `parseHttpResponse(httpResponse)`
4. `validateResponse(parsedResponse)`
5. optional `writebackResult(sourceData, parsedResponse)`
6. persist HTTP push log in `finally`

For MES-specific subclasses, do not reimplement `sendHttpRequest` when `MesBillSyncPushService` already provides the transport. Override request conversion and response validation only.

## Query, Mapping, Output, Writeback

Some sync services are composed from processor services:

- Query: `service/processor/query`
- Mapping: `service/processor/mapping`
- Output: `service/processor/output`
- Writeback: `service/processor/writeback`

For NC-to-NC or master-data synchronization, prefer the existing query/mapping/output/writeback classes instead of embedding all steps in one large service. For small bill API processors, keep logic local when that matches current project style.

## Development Checks

- Confirm whether the target project uses `com.yonyou.sync.*` or `com.yonyou.common.*` packages for shared models/repositories.
- Confirm the processor interface code in `getSupportedApiCodes` matches the route/config expected by the caller.
- Confirm the class is listed in `processors.list` if config-file registration is used.
- Confirm save action type (`WRITE`, `SAVE`, approve/delete action) matches the bill type and existing processors.
- Compile only touched classes with the local NC classpath when the full project classpath is noisy.
