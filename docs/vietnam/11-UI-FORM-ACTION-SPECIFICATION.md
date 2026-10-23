# VN-HRM | Đặc tả màn hình, biểu mẫu, datagrid và actions
**ID:** VNHRM-UI-11 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Trạng thái:** UX/SRS TO-BE. Không coi các màn hình dưới đây đã có trong code Horilla; tuân thủ design system Horilla hiện hành.

## 1. Quy tắc chung của UI
1. Mỗi màn hình bắt buộc có breadcrumb, tiêu đề, mô tả phạm vi pháp nhân/kỳ đang xem, bộ lọc, datagrid, pagination, trạng thái loading/empty/error/forbidden và hành động chính/nhóm. Không tự tạo màu/nút lệch hệ thống thiết kế.
2. Field có label tiếng Việt rõ nghĩa, đơn vị tiền/phút/ngày và giải thích khi cần. Ngày nhập dd/MM/yyyy, giờ HH:mm, VND có phân cách phần nghìn; server nhận ISO date/time và Decimal string.
3. Field required hiển thị dấu *, nhưng yêu cầu bắt buộc có điều kiện phải dựa trên workflow: Draft có thể lưu thiếu trường chưa quan trọng; Submit/Approve/Active kiểm tra bắt buộc đủ.
4. Validation chạy tại blur/submit để hỗ trợ, **bắt buộc chạy lại server-side**; lỗi đặt ngay dưới field và có summary khi nhiều lỗi. Không xóa các giá trị người dùng đã nhập khi lưu lỗi.
5. Các hành động bulk chỉ hiện khi lựa chọn phù hợp; hiển thị số bản ghi đủ điều kiện/thất bại; với nghiệp vụ không đồng nhất trạng thái, phải trả lỗi per-record, không báo thành công chung.
6. Ngày sort theo timestamp/date, tiền theo Decimal; trạng thái có chữ, icon và accessibility label, không chỉ màu. Field salary/PII không được gửi trong response nếu role không có quyền.
7. Tác vụ chốt/duyệt/từ chối/chi trả cần confirm mô tả ảnh hưởng và người thực hiện. Double-submit disabled tạm thời, server idempotency + compare-and-swap.
8. URL đính kèm qua permission-aware endpoint; không nhúng raw vault ref/CCCD trong download URL. Không lưu form PII raw ở local storage/log.
9. Khi pháp nhân đổi: reset filter ngoài scope, không trộn checkbox selection cũ, không gọi API trong phạm vi không được quyền.
10. Trang đã Paid/read-only: không hiện action chỉnh sửa trực tiếp; thay bằng yêu cầu điều chỉnh với reference kỳ gốc.

## 2. Danh mục UI và hành động chính
| UI ID | Màn hình | Field nhập/filter chính | Actions & visibility guard | Validate/UC |
|---|---|---|---|---|
| UI-VN-ORG-01 | Pháp nhân/địa điểm | code, legal_name, tax_id, tỉnh/xã, vùng, from/to | Tạo/Sửa Draft; Kích hoạt khi đủ chứng cứ | UC-ORG-001, DE-ORG-001..006 |
| UI-VN-EMP-01 | Danh sách nhân viên | staff_code, name, company, department, status | Xem/Sửa/Điều chuyển; bộ lọc theo scope | UC-EMP-001/002 |
| UI-VN-EMP-02 | Hồ sơ nhân viên | Cơ bản, công việc, pháp lý, hợp đồng, lịch sử | Lưu Draft, Gửi xác minh, Kích hoạt theo permission | UC-EMP-001/002 |
| UI-VN-DEP-01 | Người phụ thuộc | name, relationship, DOB, effective dates, verification, evidence | Khai báo, Gửi xác minh, Duyệt/Từ chối | UC-EMP-003 |
| UI-VN-CON-01 | Danh sách hợp đồng | contract_code, type, signed, start/end, wage (scope), status | Lập HĐ, Phụ lục, Gia hạn, Chấm dứt | UC-CON-001/002 |
| UI-VN-CON-02 | Phụ lục hợp đồng | amendment_code, contract, wage VND, effective_date, notes | Tạo Draft, Duyệt (khác maker), Lịch sử | UC-CON-002 |
| UI-VN-ATT-01 | Chấm công ngày | work_date, roster, in/out, source, OT, exception | Xem raw, Giải trình, Sửa công | UC-ATT-002/003 |
| UI-VN-ATT-02 | Yêu cầu sửa công | employee, work_date, source log, delta/before-after, reason, evidence | Gửi, Duyệt, Từ chối; không sửa approved | UC-ATT-003 |
| UI-VN-ATT-03 | Bảng công tháng | company, period, shift, paid hours, leave, OT, exception count | Đối soát, Chốt, Xem phiên bản | UC-ATT-005 |
| UI-VN-OT-01 | Đề nghị OT | employee, interval, work purpose, classification, actual hours | Đề nghị, Duyệt, Đối soát | UC-ATT-004 |
| UI-VN-LEV-01 | Đơn nghỉ | leave_type, from/to, halfday, requested_units, evidence | Lưu Draft, Gửi, Duyệt, Từ chối, Hủy theo trạng thái | UC-LEV-001/002 |
| UI-VN-LEV-02 | Sổ phép | employee, leave_type, period, opening/credit/debit/closing, source | Xem chứng từ, Ghi adjustment có phê duyệt | UC-LEV-002/003 |
| UI-VN-RULE-01 | Bộ công thức lương | company, code/version, from/to, inputs, parameters, golden_cases, lines | Draft/Edit/Submit/Approve/Preview/Retire | WF-PAY-RULE |
| UI-VN-PAY-01 | Kỳ lương | company, period, pay_date, tax_date, locked_attendance, status | Tạo, Preflight, Tính, Trình, Duyệt, File bank | UC-PAY-001..004 |
| UI-VN-PAY-02 | Chi tiết phiếu lương | earnings, BH NLĐ/DN, PIT, net, source, version, hash | Xem giải trình; chỉ xuất theo quyền; Paid→Adjustment | UC-PAY-002..005 |
| UI-VN-RPT-01 | Báo cáo & xuất | report_code, period, company, department, filter, requested fields | Xem/Export; audit purpose với dữ liệu nhạy cảm | UC-RPT-001 |
| UI-VN-SEC-01 | Phân quyền | user, role, company, department, fields, from/to | Grant/Revoke/History; tách phê duyệt quyền cao | UC-SEC-001 |
| UI-VN-OFF-01 | Nghỉ việc | employee, reason, effective_date, assets, balance, settlement | Tạo, Chuyển kiểm tra, Bàn giao, Chốt, Thu hồi quyền | UC-OFF-001 |

## 3. Mẫu form: F-VN-EMP-LEGAL
| Thứ tự | Field UI → API/model | Điều kiện required / edit | Kiểm tra và lỗi |
|---|---|---|---|
| 1 | Nhân viên → employee | R khi tạo, chỉ chọn đúng pháp nhân, khóa sau create | \`FIELD_REQUIRED\`, \`TENANT_SCOPE_DENIED\` |
| 2 | Pháp nhân → company | R, lấy theo assignment của NV, không cho tự chọn tenant lạ | \`REFERENCE_NOT_EFFECTIVE\` |
| 3 | Quốc tịch → nationality | R, 2 ký tự hoặc danh mục ISO theo policy | \`INVALID_FORMAT\` |
| 4 | 4 số cuối CCCD/MST/BHXH → *_suffix | Optional, đúng 4 chữ số | \`INVALID_FORMAT\`; không nhập ID đầy đủ |
| 5 | Tham chiếu vault → *_vault_ref | Optional, opaque, không whitespace/chỉ số | \`INVALID_FORMAT\`, vault policy |
| 6 | Tình trạng cư trú → residency_type | R khi dùng để tính PIT, 3 trạng thái chuẩn | \`POLICY_NOT_APPROVED\` nếu thiếu căn cứ |
| 7 | Trạng thái xác minh → verification_status | Chỉ verifier được quyền chuyển | \`VERIFICATION_REQUIRED\` nếu thiếu evidence/time |
| 8 | Ghi chú → notes | Optional; không raw sensitive ID | \`FIELD_ACCESS_DENIED\` |

**Actions:** Lưu nháp (đúng quyền), Gửi xác minh, Xác nhận/Từ chối có reviewer/evidence, Xem lịch sử (sensitive audit). **Thông điệp:** “Không thể xác minh hồ sơ: thiếu bằng chứng hoặc người phê duyệt.”

## 4. Mẫu form: F-VN-DEP
- **Fields**: Nhân viên (FK, bắt buộc, không xuyên công ty); Họ tên (max200, trim); Quan hệ (danh mục theo policy; code hiện free text); Ngày sinh (không tương lai theo rule); 4 số cuối ID (optional đúng 4 số); vault ref (opaque); từ ngày (required); đến ngày (nullable và >= from); tài liệu chứng minh (permission-aware); verification status (server controlled).
- **Dynamic UI**: thay quan hệ có thể đổi required evidence, thời gian tính quyền lợi, cảnh báo trùng; không coi đã verify chỉ vì có evidence_ref.
- **Actions**: Khai báo → Gửi xác minh → Đã xác minh/Từ chối; khi rejected bắt buộc nhập lý do; thay đổi sau Approved phải tạo event/phiên bản; không âm thầm sửa PIT Paid.
- **Errors**: DATE_RANGE_INVALID, IDENTITY_REVIEW_REQUIRED, REFERENCE_NOT_EFFECTIVE, FIELD_REQUIRED, POLICY_NOT_APPROVED.

## 5. Mẫu form: F-VN-CON-AMENDMENT
- **Fields**: company (tenant), contract (FK), amendment_code (required/max64/unique company), effective_date (required), new_monthly_wage_vnd (Decimal 17,0 không âm theo code), created_by (server), status (server), approved_by/at (server), notes.
- **UI conditional**: Approved ⇒ toàn bộ trường nội dung readonly, không hiện nút Sửa/Xóa. Không cho người lập duyệt. Ngày hiệu lực giữa kỳ phải hiển thị cảnh báo số kỳ công/lương chịu ảnh hưởng.
- **Server additional SPEC**: kiểm tra min wage theo vùng/loại HĐ, xung đột phụ lục, lương trong kỳ Paid và hiệu lực HĐ gốc.
- **Confirm**: “Phê duyệt phụ lục này không tự cập nhật mức lương trên hợp đồng gốc ở phiên bản hiện tại.” (Chỉ hiện khi adapter chưa triển khai.)
- **Errors**: CODE_DUPLICATE, VALUE_OUT_OF_RANGE, SELF_APPROVAL_DENIED, CONTRACT_OVERLAP, PAID_IMMUTABLE.

## 6. Mẫu form: F-VN-ATT-CORRECTION
- **Fields**: company, employee, work_date, source log [SPEC], trước/sau hoặc delta [SPEC], requested_minutes (int [-1440,1440] ở code), reason (required nonblank), evidence [SPEC], status, requested_by/reviewed_by/reviewed_at (server).
- **Data grid**: Mã phiếu, nhân viên, ngày công, ca, thời lượng, lý do rút gọn, requester, trạng thái, reviewer, timestamp. Không hiển thị nhãn “đã áp dụng công” chỉ vì status=approved.
- **Actions**: Submit; Approve/Reject (chỉ đúng reviewer+pending); xem log gốc; xem tác động công/lương; khóa sửa sau quyết định. Sau kỳ locked phải đi nhánh Adjustment theo WF.
- **Errors**: VALUE_OUT_OF_RANGE, FIELD_REQUIRED, TENANT_SCOPE_DENIED, PERIOD_LOCKED, SELF_APPROVAL_DENIED, INVALID_STATE_TRANSITION.

## 7. Mẫu form: F-VN-LEAVE
- **Fields**: Nhân viên, loại phép, from/to, half-day, đơn vị ngày/giờ, số ngày yêu cầu readonly-derived, số dư trước/sau, chứng cứ theo leave_type, tuyến duyệt. Nguồn chuẩn phải là lịch hiệu lực, không phải ngày dương lịch trừ thẳng.
- **Actions**: Save Draft (chưa debit), Submit, Approve/Reject, Cancel, xem ledger và impact payroll; approve/debit trong transaction.
- **Guard UI**: insufficient balance, overlap, already approved, locked/Paid, double submit. Hiển thị công thức “Dư đầu + Cấp + Điều chỉnh – Đã dùng = Dư cuối”, minh bạch từng source. Không cho xóa ledger cũ.
- **Errors**: DATE_RANGE_INVALID, LEAVE_BALANCE_INSUFFICIENT, PERIOD_LOCKED, DUPLICATE_REQUEST, PAID_IMMUTABLE.

## 8. Mẫu form: F-VN-RULESET
- **Fields**: code Slug64, version PositiveInt, title Char200, company, effective_from/to, legal_reference, status readonly, JSON parameters <=80, input_names <=80 unique, golden_cases <=50, lines (position unique/rule set, code, label, category, expression<=700, explanation).
- **Action constraints**: Draft được thêm/sửa/xóa line; Review chỉ trả lại Draft hoặc Approved; Approved khóa nội dung; Retired không sửa. Role hiện tại superuser-only; mục đích sau này cần Payroll Owner/Checker.
- **Tính thử**: textarea JSON giả lập, cảnh báo không nhập lương thật, bảng từng dòng code/category/amount; lỗi biến chưa khai báo/JSON trùng/Golden sai hiển thị rõ. Không ghi Payslip.
- **Trường hợp ranh giới**: chia 0, tên biến sai, tham chiếu trước, decimal float, version chồng hiệu lực, maker-checker, Golden Case sai 1 VND.
- **Errors**: INVALID_FORMAT, RULE_NOT_EFFECTIVE, GOLDEN_CASE_MISMATCH, SELF_APPROVAL_DENIED, INVALID_STATE_TRANSITION.

## 9. Mẫu form: F-VN-PAYROLL
- **Fields**: legal entity, period_from/to, pay_date, tax_recognition_date, locked_attendance_version, contract_version, rule_set/code/version, employee count, gross/net totals, reconciliation differences, status, source_hash, bank_reference.
- **Preflight**: per-employee issue grid phải có issue_code, severity, source, fix action, impacted amount; không cho tính chính thức nếu critical. Phân biệt preview RuleSet JSON với payroll-run calculation đã tích hợp.
- **Datagrid**: Employee, HĐ/version, công chuẩn, công hưởng, OT, phép, earnings, BH NLĐ, PIT, deductions, Net, BH DN, flags, rule version, last reconciled.
- **Actions**: Create Draft → Preflight → Calculate → Reconcile → Submit → Approve → Export Payment → Bank Confirm → Paid. Paid chỉ được tạo adjustment, không sửa tiền. Partial payment không được báo thanh toán đủ.
- **Policy**: giới hạn withholding/tax/BH/OT/minimum wage theo thời gian cần sign-off độc lập và Golden Cases.

## 10. Danh sách lỗi UX/thông báo
| Code | Message chuẩn UI |
|---|---|
| FIELD_REQUIRED | Vui lòng nhập đầy đủ thông tin bắt buộc trước khi gửi duyệt. |
| INVALID_FORMAT | Dữ liệu nhập chưa đúng định dạng của trường. |
| DATE_RANGE_INVALID | Ngày kết thúc không được trước ngày bắt đầu. |
| TENANT_SCOPE_DENIED | Bạn không có quyền thao tác trên dữ liệu của đơn vị này. |
| SELF_APPROVAL_DENIED | Người lập không được tự phê duyệt yêu cầu này. |
| PERIOD_LOCKED | Kỳ công đã khóa. Hãy tạo yêu cầu điều chỉnh có kiểm soát. |
| PAID_IMMUTABLE | Kỳ này đã thanh toán; vui lòng lập điều chỉnh cho kỳ sau. |
| RULE_NOT_EFFECTIVE | Không tìm thấy bộ quy tắc đã duyệt có hiệu lực cho thời điểm này. |
| GOLDEN_CASE_MISMATCH | Kết quả tính khác bộ dữ liệu đối soát. Không thể duyệt. |
| RECONCILIATION_FAILED | Số tiền chi tiết chưa khớp tổng đối soát; chưa thể chốt. |

## 11. Điều kiện chấp nhận màn hình
- Có screenshot/story của mỗi trạng thái Draft/Pending/Approved/Rejected/Locked/Paid nếu áp dụng; mỗi button được map actor + workflow transition.
- Có một validation TC cho required, invalid, boundary, cross-field, wrong company, wrong state; không kiểm thử chỉ “form lưu được”.
- Có API security test đảm bảo UI che trường nhạy cảm không chỉ bằng CSS và bulk action đúng quyền từng bản ghi.
- Export PDF/XLSX/CSV có i18n, totals, sorting/filtering, chống CSV injection và số tiền không sai.
- Không đánh dấu implementation completed khi màn hình còn mô tả TO-BE hoặc nằm trong Django superuser Admin đơn thuần.

Tham chiếu [UI chuẩn](09-CHUAN-HOA-GIAO-DIEN-VA-THONG-DIEP-VI.md), [Validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [Workflow](13-WORKFLOW-STATE-TRANSITIONS.md), [API](14-API-PERMISSION-ERROR-CONTRACT.md).
