# VN-HRM | Traceability, Acceptance Criteria, Test Case và Quality Gates
**ID:** VNHRM-QA-15 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Trạng thái:** Test specification; **NOT RUN** (không có bằng chứng kết quả Django/CI/UAT trong lần cập nhật tài liệu).

## 1. Quy chuẩn bằng chứng và trạng thái
- Mỗi dòng trace: \`Feature → UC → BR → DE/Field → WF transition → UI/API → Code/Migration → TC → Evidence → Sign-off\`. Mọi đoạn thiếu phải ghi **GAP/NOT IMPLEMENTED/NOT RUN**, không suy luận PASS từ sự tồn tại testcase.
- Trạng thái cho từng test: NOT_DESIGNED, DESIGNED, BLOCKED_BY_POLICY, BLOCKED_BY_CODE, NOT_RUN, PASS (kèm SHA+environment+data+output), FAIL, WAIVED có quyết định. Trạng thái triển khai code: AS_IS_VERIFIED, CODE_STATIC_ONLY, TO_BE, INTEGRATED_TESTED.
- **Test oracle**: với lương/pháp luật phải là bộ số độc lập được kế toán/pháp chế xác nhận; không lấy kết quả engine đang kiểm thử làm expected. Ghi input, version luật, ngày hiệu lực, rounding policy và phép tính độc lập.
- **Gate**: G0 code baseline, G1 dữ liệu/migration, G2 nghiệp vụ Attendance+Leave, G3 Payroll, G4 Security, G5 E2E/UAT. Không merge production nếu test critical chưa PASS hoặc có quyết định waiver hợp lệ.

## 2. Ma trận truy vết đầy đủ 23 UC
| UC | BR / DE chủ đạo | Workflow | Màn hình/API đích | Code liên quan / thực trạng | TC |
|---|---|---|---|---|---|
| UC-VN-ORG-001 | BR-VN-ORG-001/002; DE-VN-ORG-001..006 | WF-EMP prerequisite | Org forms/API [SPEC] | base.Company AS-IS; VNLegalEntity [TO-BE] | TC-ORG-001/002 |
| UC-VN-ORG-002 | BR-VN-ORG-001; DE-VN-EMP-009..011 | WF-EMP/CON | Transfer [SPEC] | EmployeeWorkInformation AS-IS; history [GAP] | TC-ORG-003 |
| UC-VN-EMP-001 | BR-VN-EMP-001/002; DE-VN-EMP-001..011 | WF-EMP | Employee create [SPEC] | employee.Employee + VNEmployeeLegalProfile [CODE STATIC] | TC-EMP-001/003 |
| UC-VN-EMP-002 | BR-VN-EMP-001/002; DE-VN-EMP-002..008 | WF-EMP | PII verify [SPEC] | vault/verification workflow [GAP] | TC-EMP-002, TC-SEC-004 |
| UC-VN-EMP-003 | BR-VN-EMP-003; DE-VN-DEP-001..005 | WF-EMP dependent | Dependent [SPEC] | VNDependent [CODE STATIC]; PIT link [GAP] | TC-DEP-001..006, TC-PIT-002/003 |
| UC-VN-CON-001 | BR-VN-CON-001; DE-VN-CON-001..005 | WF-CON | Contract [SPEC] | payroll.Contract AS-IS | TC-CON-001..003 |
| UC-VN-CON-002 | BR-VN-CON-002; DE-VN-CON-004/005 | WF-CON amendment | Amendment [SPEC] | VNContractAmendment [CODE STATIC]; apply [GAP] | TC-CON-004..009 |
| UC-VN-ATT-001 | BR-VN-ATT-002; DE-VN-ATT-002/004 | WF-ATT | Shift/Roster [SPEC] | base.EmployeeShift/Roster AS-IS | TC-ATT-004, TC-SHF-001 |
| UC-VN-ATT-002 | BR-VN-ATT-001/002; DE-VN-ATT-001..004 | WF-ATT ingest | Attendance [SPEC] | attendance.Attendance AS-IS | TC-ATT-001/003/004 |
| UC-VN-ATT-003 | BR-VN-ATT-001; DE-VN-ATT-004..006 | WF-ATT-CORR | Correction [SPEC] | VNAttendanceCorrection [CODE STATIC]; apply [GAP] | TC-ATT-002/005, TC-COR-001..007 |
| UC-VN-ATT-004 | BR-VN-ATT-003/004; DE-VN-ATT-005 | WF-OT | OT [SPEC] | AttendanceOverTime/payslip_calc AS-IS | TC-OT-001..004 |
| UC-VN-ATT-005 | BR-VN-ATT-005; DE-VN-ATT-006 | WF-ATT close | Attendance period [SPEC] | lock/snapshot [GAP] | TC-ATT-005, TC-LOCK-001 |
| UC-VN-LEV-001 | BR-VN-LEV-001; DE-VN-LEV-001..003 | WF-LEV | Leave request [SPEC] | leave.LeaveRequest AS-IS | TC-LEV-001/005 |
| UC-VN-LEV-002 | BR-VN-LEV-002; DE-VN-LEV-001..003 | WF-LEV | Leave approval [SPEC] | VNLeaveLedgerEntry [CODE STATIC]; integration [GAP] | TC-LEV-002/004, TC-LED-001..006 |
| UC-VN-LEV-003 | BR-VN-LEV-003; DE-VN-LEV-002 | WF-LEV accrual | Leave entitlement [SPEC] | AvailableLeave AS-IS; version ledger [GAP] | TC-LEV-003/006 |
| UC-VN-PAY-001 | BR-VN-PAY-001/006/007; DE-VN-PAY-001..003 | WF-PAY | Payroll run [SPEC] | payroll_run.py AS-IS; VNRuleSet [CODE STATIC] | TC-PAY-001/004/011 |
| UC-VN-PAY-002 | BR-VN-PAY-002..007; DE-VN-PAY-004..006 | WF-PAY calc | Payroll preview [SPEC] | vn_payroll.engine/services [CODE STATIC], payslip link [GAP] | TC-PAY-002/008..013, TC-RULE-001..010 |
| UC-VN-PAY-003 | BR-VN-PAY-007/008; DE-VN-PAY-003/006 | WF-PAY approval | Payroll approve [SPEC] | RuleSet approval [CODE] ≠ Payslip approval | TC-PAY-003/006 |
| UC-VN-PAY-004 | BR-VN-PAY-008; DE-VN-PAY-008 | WF-PAY payment | Bank reconcile [SPEC] | bank file / Paid workflow [GAP] | TC-RPT-004, TC-PAY-007 |
| UC-VN-PAY-005 | BR-VN-PAY-008; DE-VN-PAY-007 | WF-PAY adjustment | Payroll adjustment [SPEC] | VNPayrollAdjustment [TO-BE] | TC-PAY-003/010 |
| UC-VN-RPT-001 | BR-VN-RPT-001; DE-VN-SEC-001/002 | WF-RPT export | Report [SPEC] | report registry AS-IS, scopes need audit | TC-RPT-001..004 |
| UC-VN-SEC-001 | BR-VN-SEC-001/002; DE-VN-SEC-001/002 | WF-SEC grant | Permissions [SPEC] | new Admin superuser-only, granular grants [GAP] | TC-SEC-001..008 |
| UC-VN-OFF-001 | BR-VN-SEC-006; BR-VN-PAY-008 | WF-OFF | Offboarding [SPEC] | offboarding AS-IS, VN integration [GAP] | TC-OFF-001..004 |

## 3. Field-level tests và boundary oracle
| TC | Input/điều kiện | Expected result | Mã lỗi/đối chiếu |
|---|---|---|---|
| TC-EMP-001 | Thiếu định danh khi lập Draft, có lý do bổ sung | Có thể lưu Draft theo policy, không phát sinh CCCD giả | FIELD_REQUIRED chỉ khi Active/policy cần |
| TC-EMP-002 | Role không có sensitive field scope gọi API/export CCCD | Không trả raw; audit khi xem/export đúng quyền | FIELD_ACCESS_DENIED |
| TC-EMP-003 | Hai employee nghi trùng CCCD có vault ref khác | Không merge tự động; chuyển review | IDENTITY_REVIEW_REQUIRED |
| TC-DEP-001 | dependent eligible_to < eligible_from | Không lưu | DATE_RANGE_INVALID |
| TC-DEP-002 | identity_suffix = 123 / 12345 / ký tự chữ | Bị từ chối; đúng 4 chữ số thì nhận | INVALID_FORMAT |
| TC-DEP-003 | full_name chỉ dấu cách/relationship ngoài danh mục | Không cho gửi xác minh | FIELD_REQUIRED/INVALID_FORMAT (SPEC) |
| TC-DEP-004 | verified không có reviewer/evidence | Không được tính giảm trừ (POLICY) | VERIFICATION_REQUIRED |
| TC-DEP-005 | Cùng dependent, hai eligibility overlap | Chặn hoặc reviewer xử lý theo policy, không tính hai lần | EFFECTIVE_DATE_OVERLAP |
| TC-DEP-006 | identity_vault_ref toàn số hoặc có whitespace | Từ chối | INVALID_FORMAT [CODE] |
| TC-CON-001 | Phụ lục giữa kỳ, lương mới áp hiệu lực | Prorate kỳ có hai mức, không đổi kỳ Paid cũ | POLICY golden |
| TC-CON-002 | HĐ xung đột hiệu lực | Chặn trước active/payroll | CONTRACT_OVERLAP |
| TC-CON-003 | Mức lương dưới tối thiểu vùng/giờ theo hiệu lực | Block/warn theo rule pháp lý đã duyệt, không lấy vùng hiện tại cho quá khứ | POLICY_NOT_APPROVED nếu thiếu nguồn |
| TC-CON-004 | Phụ lục đã approved sửa wage/code | Từ chối | PAID_IMMUTABLE/INVALID_STATE_TRANSITION |
| TC-CON-005 | amendment_code giống trong cùng company | DB không tạo bản trùng | CODE_DUPLICATE |
| TC-CON-006 | amendment_code giống hai company | Theo uniqueness composite thì không xung đột, nhưng phải scope API | TENANT_SCOPE_DENIED khi đọc chéo |
| TC-CON-007 | wage=-1, wage=0, decimal có phần lẻ | Âm từ chối; 0 và số lẻ cần policy/scale xác định | VALUE_OUT_OF_RANGE |
| TC-CON-008 | created_by = approved_by | Không được approve | SELF_APPROVAL_DENIED |
| TC-CON-009 | Approved amendment chưa áp lên HĐ | Không báo HĐ đã đổi; tạo GAP integration | BLOCKED_BY_CODE |
| TC-SHF-001 | Ca 22:00–06:00 qua hai ngày | Giữ work_date theo ca đã duyệt, không nhân đôi công | Calendar version |
| TC-COR-001 | requested_minutes = -1441/+1441 | Không lưu | VALUE_OUT_OF_RANGE [CODE] |
| TC-COR-002 | requested_minutes = -1440,0,1440 | Trong range CODE, tính hợp lý theo ca cần policy | POLICY edge |
| TC-COR-003 | reason toàn whitespace | Không lưu | FIELD_REQUIRED [CODE] |
| TC-COR-004 | Reviewer=requester | Không duyệt | SELF_APPROVAL_DENIED [CODE nếu requester tồn tại] |
| TC-COR-005 | Đã approved thử sửa reason/status | Không sửa đè | INVALID_STATE_TRANSITION [CODE] |
| TC-COR-006 | Employee company khác Correction company | Phải từ chối [SPEC, clean chưa thể hiện] | TENANT_SCOPE_DENIED |
| TC-COR-007 | Công Locked/Paid muốn sửa công | Không mutate Attendance/Payslip Paid; tạo delta | PERIOD_LOCKED/PAID_IMMUTABLE |
| TC-ATT-001 | Cùng source+event id gửi 2 lần | Raw sự kiện duy nhất | DUPLICATE_REQUEST |
| TC-ATT-003 | Thiếu log out | Tạo exception, không tự điền 8h | Missing event |
| TC-ATT-004 | Ca qua nửa đêm, loại ngày thay đổi | Giờ, OT và work_date theo rule phiên bản | POLICY |
| TC-ATT-005 | Chốt kỳ còn phiếu sửa công pending | Không lock nếu ngoại lệ chưa xử lý/waiver | ATTENDANCE_NOT_LOCKED |
| TC-OT-001 | Hai loại OT cùng phút | Phút chỉ trả một lần | RECONCILIATION_FAILED |
| TC-OT-002 | OT ngày lễ + ca đêm | Phân đoạn theo rule đã duyệt, không nhân phẳng | Golden OT |
| TC-OT-003 | Request 3h, confirmed actual 2h | Chỉ trả theo giao thời lượng và chính sách | Golden OT |
| TC-OT-004 | Vượt giới hạn OT theo loại lao động/tháng/năm | Block/đưa phê duyệt đặc thù nếu luật cho phép | POLICY |
| TC-LED-001 | units=0 | Không lưu | VALUE_OUT_OF_RANGE [CODE] |
| TC-LED-002 | Trùng source_key trong company | Không tạo ledger thứ 2 | CODE_DUPLICATE [CODE] |
| TC-LED-003 | Sửa/xóa instance đã tạo | Không cho phép | INVALID_STATE_TRANSITION [CODE] |
| TC-LED-004 | QuerySet bulk delete/update | Cần hardening lớp DB/service; chưa khẳng định chặn | SECURITY GAP |
| TC-LED-005 | Hai lần approve cùng request song song | Debit đúng một lần, balance đúng | Idempotency + locking [SPEC] |
| TC-LED-006 | Hủy approved request hợp lệ | Credit đúng một lần, không xóa debit | SPEC |
| TC-LEV-001 | Đơn nửa ngày trên ca khác 8h | Balance theo chính sách ngày/giờ nhất quán | POLICY |
| TC-LEV-002 | Approve retry | Debit một lần | Ledger source id |
| TC-LEV-003 | Carryforward hết hạn | Có bút toán expire, giữ lịch sử | Ledger reconcile |
| TC-LEV-004 | Hủy phép sau Paid | Không sửa payslip Paid; phát adjustment | PAID_IMMUTABLE |
| TC-LEV-005 | Nghỉ ốm hưởng chế độ BH | Không tự gán 100% lương do doanh nghiệp trả | POLICY |
| TC-LEV-006 | Vào giữa năm/thâm niên | Prorate và accrual theo bảng chính sách duyệt | Golden leave |
| TC-RULE-001 | Syntax truy cập \`a.__class__\` / import | Formula bị từ chối trước tính | FormulaError [CODE] |
| TC-RULE-002 | Formula chia 0 hoặc input non-finite | Không tính, trả lỗi rõ | FormulaError [CODE] |
| TC-RULE-003 | Input thiếu/thừa biến | Preview từ chối | FIELD_REQUIRED/INVALID_FORMAT [CODE] |
| TC-RULE-004 | Input ghi đè parameters | Từ chối | INVALID_FORMAT [CODE] |
| TC-RULE-005 | Code tham chiếu dòng chưa tính | Không duyệt | RULE_DEPENDENCY_INVALID [CODE] |
| TC-RULE-006 | Golden Cases expected lệch 1 VND | Không duyệt | GOLDEN_CASE_MISMATCH [CODE] |
| TC-RULE-007 | Creator tự approve hoặc thiếu legal reference | Không duyệt | SELF_APPROVAL_DENIED/FIELD_REQUIRED [CODE] |
| TC-RULE-008 | Hai approved cùng company/code/effective_from | Không cho duyệt phiên bản trùng ngày | EFFECTIVE_DATE_OVERLAP [CODE] |
| TC-RULE-009 | Approved thử thay expression/parameters | Chặn; tạo version mới | INVALID_STATE_TRANSITION [CODE] |
| TC-RULE-010 | Retire qua Admin menu | Phải khả dụng sau khi đăng ký action; hiện GAP | BLOCKED_BY_CODE |
| TC-PAY-001 | Attendance chưa locked | Không tạo payroll chính thức | ATTENDANCE_NOT_LOCKED |
| TC-PAY-002 | Cùng input/rule/rounding version | Gross/Net các lần giống nhau đến đồng | Golden |
| TC-PAY-003 | Sửa payslip Paid | Không sửa; adjustment riêng | PAID_IMMUTABLE |
| TC-PAY-004 | Rule chưa duyệt/chưa có hiệu lực | Không phát hành payslip | RULE_NOT_EFFECTIVE |
| TC-PAY-006 | Payline thiếu source/rule version | Không cho chốt | RECONCILIATION_FAILED |
| TC-PAY-007 | Bank nhận 99/100 giao dịch | Không Paid cả 100, thể hiện partially paid | RECONCILIATION_FAILED |
| TC-PAY-008 | PIT ở 10/10.01/30/30.01/60/100/100.01 triệu | Thuế đúng từng bậc theo rule phiên bản ký duyệt | Golden PIT, không hardcode |
| TC-PAY-009 | Allowance taxability khác insurance-ability | Xác định hai thuộc tính độc lập | Golden payroll |
| TC-PAY-010 | Kỳ cũ rule A, kỳ mới B | Recompute kỳ cũ vẫn A từ snapshot | Snapshot version |
| TC-PAY-011 | Tạo run cùng Idempotency-Key hai lần | Chỉ một run | DUPLICATE_REQUEST |
| TC-PAY-012 | Nonresident | Không dùng công thức resident nếu chưa xác nhận | POLICY |
| TC-PAY-013 | Nghỉ việc giữa kỳ | Chia khoảng có hiệu lực, thanh toán theo policy | Golden payroll |
| TC-SEC-001 | Actor company A request object company B | 403/404, không lộ existence | TENANT_SCOPE_DENIED |
| TC-SEC-002 | Actor không quyền lương gọi dashboard/export | Không có dữ liệu tiền cả JSON/file | FIELD_ACCESS_DENIED |
| TC-SEC-003 | Maker duyệt lương của mình | Chặn self approval | SELF_APPROVAL_DENIED |
| TC-SEC-004 | Export PII có quyền | Audit actor/time/scope, không log nguyên định danh | Audit |
| TC-SEC-005 | Offboarding | Revoke session/refresh token tại thời điểm policy | Security |
| TC-SEC-006 | CSV cell bắt đầu =,+,-,@ | Escape, không thực thi spreadsheet formula | CSV injection |
| TC-SEC-007 | URL đính kèm đoán được | Không truy cập vượt scope | Access denied |
| TC-SEC-008 | Infra admin không có payroll grant | Không xem raw payroll qua UI/API/report | Deny-by-default |
| TC-OFF-001 | Đúng ngày rời công ty | Trạng thái/quyền thay đổi theo effective date | Workflow |
| TC-OFF-002 | Còn công nợ hoặc tài sản chưa bàn giao | Không đánh dấu checklist hoàn tất sai | Policy |
| TC-OFF-003 | Settlement thiếu phép/OT | Cảnh báo và chặn Paid nếu không có waiver | Payroll reconciliation |
| TC-OFF-004 | Đổi ngày nghỉ sau payroll Paid | Delta kỳ sau, giữ snapshot | PAID_IMMUTABLE |

## 4. Bộ chứng cứ cần lưu cho mỗi lần chạy
| Cột | Nội dung |
|---|---|
| TC ID / UC / Field | Một TC có thể có nhiều bước nhưng expected mỗi bước rõ |
| Build | Repo, branch, commit SHA, migration state, settings checksum, môi trường và Python/Django version |
| Data | Fixtures tổng hợp, company roles, policy/rule versions, effective dates, timezone |
| Actual vs Expected | Số tiền, số dư, trạng thái, response code/message, số dòng DB thay đổi |
| Security | Actor, token scope, request path, payload đã mask, audit event |
| Result | PASS/FAIL/BLOCKED/NOT RUN; screenshot/log redacted, timestamp, reviewer |
| Decision | Bug ID, severity, owner, target PR, waiver/legal decision nếu có |

## 5. Quy tắc duyệt Release
G0: baseline Horilla 2.0; G1: migration, constraints, import; G2: ATS, HĐ, công/OT/phép; G3: rule version, golden payroll, bảo hiểm/PIT và bank; G4: field/tenant IDOR, audit/vault; G5: UAT thực tế ký bởi HR/Payroll/Finance/Pháp chế, backup/restore, pilot.

**Không sign-off** khi còn contract/attendance/leave/payroll integration GAP critical, người phê duyệt policy chưa được xác định, hoặc có bất kỳ TC critical với evidence NOT RUN mà bị đánh dấu PASS.

Liên kết: [UC](12-USE-CASE-DETAILS.md), [Validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [Workflow](13-WORKFLOW-STATE-TRANSITIONS.md), [API](14-API-PERMISSION-ERROR-CONTRACT.md), [GAP code](16-CODE-TO-DOC-GAP.md).
