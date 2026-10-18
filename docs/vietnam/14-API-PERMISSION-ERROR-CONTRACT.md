# VN-HRM | Hợp đồng API, phân quyền, mã lỗi và audit
**ID:** VNHRM-API-14 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Trạng thái:** SPEC/TO-BE; endpoint mô tả ở đây là hợp đồng đề xuất, KHÔNG khẳng định đã tồn tại trong Horilla.

## 1. Quy tắc thiết kế
- API versioning dưới \`/api/vn/v1/\` chỉ là định hướng, phải đối chiếu router Horilla trước khi implement. Không ghi đè endpoint legacy nếu chưa có regression test.
- Mọi resource scoped bởi company tại server qua membership/scope hợp lệ, object-level permissions và field-level access. Company ID do client gửi chỉ là tham số lọc, không quyết định quyền.
- API list/search/count/dashboard/export/download đều phải dùng cùng cơ chế scope; data được mask trước serialize, không chỉ ẩn DOM.
- Các thao tác có tiền/số dư/chốt/phê duyệt: yêu cầu \`Idempotency-Key\` cho mutation có retry, \`If-Match\`/revision cho chuyển trạng thái cạnh tranh, transaction atomic và audit trong cùng giao dịch. Không trả thành công trước khi ghi vững bền.
- Response chứa \`request_id\`/\`correlation_id\`; validation trả lỗi theo field và business rule với mã không phụ thuộc ngôn ngữ. Error message tiếng Việt dùng cho giao diện; không lộ dữ liệu của tenant khác.
- Mọi datetime API dạng ISO 8601 kèm offset; \`effective_date\` là YYYY-MM-DD; tiền Decimal truyền dạng chuỗi, không dùng số floating-point trong JSON chính thức. VND ở UI dùng phân tách theo ngôn ngữ, API không gắn ký hiệu tiền.
- Chỉ ghi snapshot/hash của nguồn có quyền truy xuất; không log salary inputs/CCCD/MST/BHXH/bank number/token.

## 2. Định nghĩa lỗi chuẩn (đề xuất)
~~~json
{
  "error": {
    "code": "FIELD_REQUIRED",
    "message": "Vui lòng nhập ngày bắt đầu hiệu lực.",
    "field_errors": [
      {"field": "effective_from", "code": "FIELD_REQUIRED", "message": "Trường này là bắt buộc."}
    ],
    "resource_id": null,
    "correlation_id": "request-or-event-id",
    "retryable": false
  }
}
~~~
- 400: JSON sai, thiếu header bắt buộc, giá trị không parse được.
- 401: chưa xác thực hoặc phiên hết hạn.
- 403: có danh tính nhưng không đủ quyền, không trả dữ liệu bản ghi không thuộc scope.
- 404: bản ghi không tồn tại **hoặc** không được phép biết tồn tại trong các trường hợp chống enumeration.
- 409: trùng, state conflict, version stale, locked, Paid.
- 422: dữ liệu đúng cú pháp nhưng vi phạm quy tắc nghiệp vụ, policy chưa có, rule không hiệu lực.
- 429: rate limit theo endpoint/actor; 500 chỉ cho lỗi bất ngờ, không thay thế 4xx nghiệp vụ.

| Mã lỗi | Điều kiện điển hình | HTTP | Hiển thị/giải pháp |
|---|---|---:|---|
| FIELD_REQUIRED | Field bắt buộc trống/null sai policy | 422 | Nêu đúng tên trường và điều kiện |
| INVALID_TYPE | Sai numeric/date/enum | 422 | Hướng dẫn kiểu dữ liệu |
| INVALID_FORMAT | Sai mẫu/ngày/timezone/JSON | 422 | Nêu định dạng kỳ vọng, tránh hiện dữ liệu PII |
| VALUE_OUT_OF_RANGE | Số/độ dài vượt ngưỡng | 422 | Nêu min/max đã được quyết định |
| DATE_RANGE_INVALID | Ngày kết thúc < bắt đầu | 422 | Yêu cầu kiểm tra khoảng |
| REFERENCE_NOT_EFFECTIVE | FK/địa giới/HĐ/lịch hết hiệu lực | 422 | Chọn bản có hiệu lực |
| CODE_DUPLICATE | Trùng mã trong phạm vi U(scope) | 409 | Không làm lộ pháp nhân khác |
| IDENTITY_REVIEW_REQUIRED | Nghi trùng định danh nhạy cảm | 422 | Mở đối soát bảo mật |
| TENANT_SCOPE_DENIED | Vượt phạm vi pháp nhân | 403/404 | Không tiết lộ owner data |
| FIELD_ACCESS_DENIED | Xem/sửa trường nhạy cảm trái quyền | 403 | Không trả raw field |
| SELF_APPROVAL_DENIED | Maker tự phê duyệt | 403/422 | Yêu cầu checker độc lập |
| INVALID_STATE_TRANSITION | Hành động sai trạng thái | 409 | Refresh trạng thái |
| STATE_CONFLICT | Revision lạc hậu/duyệt đồng thời | 409 | Nạp lại và xử lý |
| PERIOD_LOCKED | Bảng công đã khóa | 409 | Điều chỉnh kỳ có kiểm soát |
| PAID_IMMUTABLE | Phiếu Paid bị yêu cầu sửa | 409 | Delta kỳ sau |
| CONTRACT_OVERLAP | Hai hợp đồng hiệu lực trái policy | 422 | Giải quyết xung đột trước calculate |
| RULE_NOT_EFFECTIVE | Không có đúng một rule approved hợp lệ | 422 | Chờ cấu hình/duyệt rule |
| POLICY_NOT_APPROVED | Chính sách đang chờ xác nhận | 422 | Không áp mặc định trái căn cứ |
| GOLDEN_CASE_MISMATCH | Expected ≠ calculated | 422 | Không phê duyệt ruleset |
| ATTENDANCE_NOT_LOCKED | Chưa chốt công kỳ | 422 | Chốt công trước |
| LEAVE_BALANCE_INSUFFICIENT | Số dư không đáp ứng quy chế | 422 | Hủy/đổi loại hoặc xin ngoại lệ theo policy |
| REJECTION_REASON_REQUIRED | Từ chối thiếu lý do | 422 | Nhập lý do |
| DUPLICATE_REQUEST | Lặp action khác payload/cùng idempotency key | 409 | Truy vấn request gốc, không ghi đôi |
| RECONCILIATION_FAILED | Tổng dòng/tiền trả lệch | 422 | Đối soát các dòng trước chốt |
| EXTERNAL_SYNC_PENDING | Downstream chưa xác nhận | 202/409 theo action | Thể hiện pending, không đánh dấu Paid |

## 3. Ma trận quyền hành động (TO-BE)
**Ký hiệu:** O = own, T = nhân viên trực thuộc được phân quyền, C = company/assigned scope, M = mask/read-only, A = approve theo ủy quyền có hiệu lực, — = deny. Quyền tác nghiệp thực tế = Role ∩ Tenant ∩ Org/Team ∩ Field ∩ Action ∩ EffectiveDate, và SoD. Không có quyền thì không gửi dữ liệu nhạy cảm tới frontend.

| Resource / Action | Employee | Manager | HR | Payroll | HR/Pay Approver | Finance | Security Admin |
|---|---|---|---|---|---|---|---|
| Hồ sơ nhân sự cơ bản – View | O | T | C | giới hạn C | theo nhiệm vụ | — | cấu hình, không mặc nhiên PII |
| Hồ sơ định danh – raw View | —/theo xác minh danh tính | — | C có field grant | C có field grant | M | M | — |
| Hồ sơ – Create/Update | self fields giới hạn | — | C | — | — | — | — |
| Người phụ thuộc – Submit | O | — | C | C (verify) | — | — | — |
| Người phụ thuộc – Verify | — | — | phân công C | phân công C | — | — | — |
| Hợp đồng/phụ lục – Draft | — | đề nghị T | C | — | — | — | — |
| Hợp đồng/phụ lục – Approve | — | — | ủy quyền A | — | A | — | — |
| Attendance raw – View | O | T | C | C summary | — | — | — |
| Sửa công – Request | O | T theo phân công | C | — | — | — | — |
| Sửa công – Approve/Reject | — | A cho T | A cho C | — | — | — | — |
| Nghỉ – Request/Cancel | O | T theo chính sách | C | — | — | — | — |
| Nghỉ/OT – Approve | — | A cho T | A theo scope | — | — | — | — |
| Chốt công | — | xác nhận T | A cho C | read C | — | — | — |
| Ledger phép – Read/Adjust | O summary | T summary | C được cấp | C đọc phù hợp | A cho adjustment | — | — |
| RuleSet – Draft | — | — | — | C config | A review | — | kỹ thuật không tự thay rule |
| RuleSet – Approve | — | — | — | — | A khác người tạo | — | — |
| Payroll batch – Calculate | — | — | — | C | — | — | — |
| Payroll batch – Approve | — | — | — | — | A | — | — |
| Payslip – View | O | — | — | C | A | C theo payment | — |
| Payment – Export/Reconcile | — | — | — | chuẩn bị C | — | C | — |
| Report – Export | O hạn chế | T summary | C HR | C payroll | assigned | C finance | — |
| RBAC – Grant/Revoke | — | — | — | — | — | — | A security governance |
| Audit / Sensitive access | bản thân hạn chế | — | audit được cấp | audit được cấp | reviewer được cấp | — | security auditor được cấp |

**CODE NOW:** Django Admin của \`vn_hrm\`/\`vn_payroll\` đang superuser-only, chưa có ma trận role trên. Không được bật các cột quyền trước khi RBAC + tenant/field tests PASS.

## 4. Endpoint contract dự kiến và tác động
| UC | Method / path minh họa | Validation đặc thù | Thành công | Trạng thái triển khai |
|---|---|---|---|---|
| ORG-001 | POST /legal-entities | tenant grants, unique code, legal effective dates | 201 Draft | SPEC |
| EMP-001 | POST /employees | duplicate identity review, company scope | 201 Draft | SPEC |
| EMP-003 | POST /employees/{id}/dependents | eligible range, evidence, identity review | 201 pending | SPEC/Admin model exists |
| CON-002 | POST /contracts/{id}/amendments | wage, amendment code, effective date | 201 draft | SPEC/Admin model exists |
| CON-002 | POST /amendments/{id}/approve | If-Match, maker-checker, policy guard | 200 approved | SPEC/Admin action exists |
| ATT-003 | POST /attendance-corrections | source log, period lock, reason | 201 pending | SPEC/Admin model exists |
| ATT-003 | POST /attendance-corrections/{id}/decide | reviewer scope, status, reason | 200 decided | SPEC/Admin action exists |
| LEV-001 | POST /leave-requests | calendar, overlap, balance, evidence | 201 submitted | Horilla legacy requires mapping |
| LEV-002 | POST /leave-requests/{id}/approve | key, row lock, exactly-once ledger debit | 200 approved | SPEC |
| ATT-005 | POST /attendance-periods/{id}/lock | all exception cleared, scope, hash | 200 locked | SPEC |
| PAY-001 | POST /payroll-runs | locked attendance, approved ruleset, idempotency | 201 Draft | SPEC |
| PAY-002 | POST /payroll-runs/{id}/calculate | snapshot version, Decimal, golden basis | 200 calculated | SPEC |
| PAY-003 | POST /payroll-runs/{id}/approve | SoD, balance, source hash | 200 approved | SPEC |
| PAY-004 | POST /payroll-runs/{id}/bank-reconcile | bank ref and amounts, partial state | 200 partial/paid | SPEC |
| PAY-005 | POST /payroll-adjustments | original payslip and delta | 201 Draft | SPEC |
| PAY-RULE | POST /payroll-rule-sets/{id}/preview | JSON allowed inputs, no side effects | 200 preview | Django Admin custom view [CODE], not this REST endpoint |
| SEC-001 | POST /access-grants | role/company/field/effectivity/SoD | 201 pending/active | SPEC |
| RPT-001 | GET /reports/{code}/export | field scope/tenant/export audit | 200 file/job | SPEC |

## 5. Hợp đồng audit & event
**Audit fields:** event_id (UUID), correlation_id, event_type, object_type/object_id, company_id, actor_user_id, actor_role_snapshot, occurred_at_utc, recorded_at_utc, effective_date, old_state/new_state, change_summary_masked, reason_code, source_id, policy_version, rule_version, request_fingerprint. Chỉ lưu old/new ở dạng tối thiểu và bảo vệ; không log PII gốc.

**Domain events:** EmployeeActivated, EmploymentTransferred, ContractApproved, AmendmentApplied, AttendanceCorrectionApproved, AttendancePeriodLocked, LeaveApproved, LeaveCancelled, LeaveLedgerPosted, OvertimeReconciled, PayrollRunApproved, PayslipPaid, PayrollAdjustmentCreated, AccessGrantRevoked. Event phải outbox-driven khi có downstream side effect, retry không nhân đôi.

## 6. Export/import/notification
- **Import**: dry-run, bản báo lỗi theo dòng/cột, giữ original external row id, thực hiện theo nhóm transaction; không overwrite dữ liệu Paid; cấm công thức Excel/CSV injection.
- **Export**: áp cùng quyền as-of-date và tenant scope; xin reason khi xuất PII/payroll; audit số record, filters, checksum, policy; liên kết tải hết hạn/đòi xác thực.
- **Thông báo**: chỉ gửi trạng thái và liên kết đăng nhập, không gửi salary/CCCD raw trong email body; nội dung lỗi địa phương hóa tiếng Việt.
- **Rate limiting/security**: kiểm soát scraping hồ sơ, brute force, CSRF với session, JWT replay, SSRF tệp đính kèm, URL guessed; kiểm thử IDOR ở detail, list, aggregate, export.

## 7. DoR API
Endpoint không READY nếu chưa có OpenAPI schema, mock request/response, validation DE, error code, authorization matrix, transaction/idempotency policy, negative tests, audit/retention, mapping đến hàm code cũ/mới. Spec ở đây chỉ định nghĩa contract đích; khi thực thi phải kiểm tra endpoint thực tế và migration compatibility.

Liên kết: [Validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [UC](12-USE-CASE-DETAILS.md), [Workflow](13-WORKFLOW-STATE-TRANSITIONS.md), [Traceability](15-TRACEABILITY-UAT-MATRIX.md).
