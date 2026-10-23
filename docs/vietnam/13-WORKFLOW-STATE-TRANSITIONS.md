# VN-HRM | Workflow, State Machine, Guard, Saga và Exception
**ID:** VNHRM-WF-13 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Trạng thái:** TO-BE trừ các dòng [CODE], chưa áp dụng tự động vào lõi Horilla.

## 1. Quy định chung
- **Trigger** chỉ chuyển trạng thái khi actor có permission và data scope, source state khớp phiên bản đang lưu, guard hợp lệ, transaction commit thành công, audit và outbox đã ghi. Không tin vào trạng thái do client truyền.
- **Guard** trả mã ổn định theo [hợp đồng API](14-API-PERMISSION-ERROR-CONTRACT.md), ghi lỗi vào request; nếu lỗi có thể xử lý thì không mất dữ liệu nháp.
- **Đánh dấu:** [CODE] xác minh ở nhánh \`feature/vn-dynamic-hrm\` mã model/admin; [SPEC] mô tả TO-BE; [POLICY] phụ thuộc người có thẩm quyền phê duyệt.
- **Kỳ khóa/đã Paid:** không sửa đè số liệu quá khứ; reopen có approval riêng nếu chưa thanh toán; nếu đã Paid thì phát sinh adjustment ở kỳ sau.
- **SoD:** người đề nghị/người duyệt và người tạo/người chốt tách biệt khi nghiệp vụ yêu cầu, không chỉ ẩn nút trên frontend.
- **Thời gian:** recorded_at/occurred_at/effective_at tách biệt. Tất cả thao tác có \`event_id\`, \`correlation_id\`, \`company_id\`, version và source reference.

## 2. WF-EMP — Hồ sơ nhân viên / thông tin pháp lý [SPEC]
| Từ → Đến | Action / actor | Guard / validation | Tác động atomically / lỗi |
|---|---|---|---|
| Chưa có → Draft | HR Create | Quyền company, mã NV không trùng, tối thiểu tên/pháp nhân | Tạo employee Draft; \`EMP_CODE_DUPLICATE\` |
| Draft → PendingVerification | HR Submit | Nhập đủ DE theo nhóm lao động, liên kết HĐ/vault theo policy | Đóng draft edit có version; \`FIELD_REQUIRED\` |
| PendingVerification → Active | HR Verifier Approve | maker-checker; xác minh định danh; assignment/HĐ/lịch hiệu lực | Ghi hồ sơ verified, kích hoạt, audit; \`VERIFICATION_REQUIRED\` |
| PendingVerification → Draft | Verifier Return | Lý do bắt buộc và field chưa hợp lệ | Yêu cầu bổ sung; \`REJECTION_REASON_REQUIRED\` |
| Active → Suspended | HR Authorized Suspend | Căn cứ, from/to, quyết định | Cập nhật trạng thái + revocation policy |
| Active → Offboarded | WF-OFF Complete | Đã hoàn thành điều kiện offboarding/settlement | Ngừng quyền, snapshot; không xóa bản ghi |
| Offboarded → Archived | Records Officer | Theo retention policy, không còn legal hold | Archive có audit; không hard delete |

**Đối chiếu code:** \`VNEmployeeLegalProfile\` hiện có \`verification_status=pending/verified\` và \`residency_type\`, chưa có toàn bộ transitions/tài liệu xác minh/nhân viên Active ở trên. Không thay đổi \`Employee\` chỉ bằng trạng thái pháp lý.

## 3. WF-CON — Hợp đồng / phụ lục
| Từ → Đến | Action / actor | Guard / validation | Tác động / lỗi |
|---|---|---|---|
| Draft → PendingApproval | HR Submit [SPEC] | Số HĐ unique đúng scope, thời hạn hợp lệ, min wage, policy và chứng cứ | Khóa bản đề nghị; \`CONTRACT_INVALID\` |
| PendingApproval → Approved | Signatory Approve [SPEC] | Khác người lập; quyền đúng pháp nhân/ngày, không overlap | Ghi actor/time/evidence |
| Approved → Active | Scheduler [SPEC] | signed, ngày hiệu lực đến, không có xung đột | Cập nhật assignment/hợp đồng theo lịch |
| Active → Expired/Terminated | Scheduler/HR [SPEC] | Ngày hết hạn hoặc quyết định chấm dứt | Lưu event, bắt đầu WF-OFF khi applicable |
| Amendment Draft → Approved | Contract Approver [CODE] | \`new_monthly_wage_vnd >= 0\`; khác người lập; thời điểm duyệt, company match | Khóa sửa đè; \`SELF_APPROVAL_DENIED\` |
| Amendment Approved → Applied | Integration Job [SPEC] | Ngày hiệu lực và HĐ gốc phù hợp; không đổi kỳ Paid | Tạo version lương áp dụng, phát payroll re-evaluation |
| Amendment Approved → Superseded | HR [SPEC] | Quyết định phụ lục mới/hủy hợp lệ; không edit approved | Thêm phiên bản mới, audit |

**GAP quan trọng:** PR #3 có 2 trạng thái \`draft/approved\` cho Amendment, và không tự cập nhật \`payroll.Contract.wage\`; SRS không được ghi là đã có bước Applied.

## 4. WF-ATT — Công, giải trình và khóa kỳ
| Từ → Đến | Action / actor | Guard / validation | Tác động / lỗi |
|---|---|---|---|
| RawReceived → Accepted | Device ingest [SPEC] | source/event id duy nhất, chữ ký, timestamp hợp lệ, mapping người | Raw immutable; duplicate trả existing |
| RawReceived → Quarantined | Ingest [SPEC] | Thiếu người/thiết bị/timezone; lỗi nguồn | Không phát công giả, lưu lý do |
| Open → Reconciled | HR Reconcile [SPEC] | Tổng hợp lịch, raw, OT, leave, correction không còn lỗi chặn | Snapshot per employee/day |
| Reconciled → Locked | HR Close [SPEC] | Quyền; exception threshold theo policy; review; hash input | \`attendance_period_version\` bất biến |
| Locked → Reopened | Authorized HR [SPEC] | Chưa Paid, có lý do, phê duyệt, version mới | Reopen để sửa, audit đầy đủ |
| Locked + Paid → AdjustmentNeeded | Payroll/HR [SPEC] | Có điều chỉnh hợp lệ tác động kỳ Paid | Delta kỳ sau, không sửa paid snapshot |

### WF-ATT-CORR — Phiếu sửa công
| Từ → Đến | Action/actor | Guard | Tác động |
|---|---|---|---|
| Không có → pending | Employee/HR submit [CODE Admin] | reason không rỗng; minutes trong [-1440,1440], ngày và nhân viên hợp lệ | Lưu request, người yêu cầu |
| pending → approved | Reviewer [CODE Admin] | khác requester nếu requester có; reviewer/time bắt buộc | Ghi quyết định; **chưa update Attendance** |
| pending → rejected | Reviewer [CODE Admin] | khác requester; reviewer/time bắt buộc | Ghi quyết định; cần bổ sung rejection_reason [SPEC] |
| approved → AppliedToAttendance | Adapter [SPEC] | source log, before/after, locked-state, idempotency | Ghi kết quả công không sửa raw |
| rejected/approved → edited | Không cho phép [CODE] | processed immutable | \`INVALID_STATE_TRANSITION\` |
| locked-period → CorrectionRequest | Authorized HR [SPEC] | policy reopening/payroll delta | Tách khỏi chỉnh trực tiếp công Paid |

**Lỗi cần xử lý:** company của AttendanceCorrection chưa được validate xuyên employee trong \`clean()\`; thiếu source_log, proof, before/after, rejection reason; yêu cầu UI và integration còn SPEC.

## 5. WF-OT — Làm thêm giờ [SPEC/POLICY]
| Từ → Đến | Actor/action | Guard | Side effect |
|---|---|---|---|
| Draft → Submitted | Employee | Đủ thời điểm, lý do, địa điểm, loại OT và lịch | Lưu request |
| Submitted → PendingApproval | System | Kiểm tra trùng giờ, giới hạn, đối tượng theo luật/chính sách | Chặn hoặc phân luồng ngoại lệ hợp lệ |
| PendingApproval → Approved/Rejected | Manager | Role/scope; không self approve; từ chối có reason | Audit quyết định |
| Approved → ActualReconciled | Attendance engine | Giờ thực tế confirmed và intersection với OT được duyệt | Tách loại ngày/đêm/lễ, tránh trùng |
| ActualReconciled → IncludedInPayroll | Payroll adapter | Công Locked và rule OT có hiệu lực | Snapshot source + amount |
| Paid OT changed → PayrollAdjustment | Payroll | Thời gian hoặc phân loại thay đổi sau Paid | Delta kỳ sau |

## 6. WF-LEV — Nghỉ phép, ledger và hủy
| Từ → Đến | Action/actor | Guard | Side effect |
|---|---|---|---|
| Draft → Submitted | Employee | Ngày/giờ hợp lệ, lịch hiệu lực, không overlap trái policy, minh chứng | Lưu số ngày tính được, KHÔNG debit |
| Submitted → PendingApproval | Workflow engine | Xác định tuyến theo HR/Manager và delegation | Gửi thông báo |
| PendingApproval → Approved | Approver | Quyền, trạng thái, đủ entitlement, compare-and-swap | Trong một transaction ghi ledger debit U(company,source_key) và cập nhật công |
| PendingApproval → Rejected | Approver | Lý do bắt buộc | Không debit |
| Submitted/PendingApproval → Cancelled | Employee/HR | Chính sách rút đơn, chưa approved | Không hoàn phép vì chưa debit |
| Approved → CancelRequested | Employee/HR | Điều kiện hủy và kỳ công/payroll chưa Paid | Tạo yêu cầu bù; không xóa debit |
| CancelRequested → Cancelled | Approver | Quyền, cùng source request, không retry credit | Ghi credit với source_key đảo U, cập nhật công |
| Approved/Paid → PayrollAdjustment | Authorized HR/Payroll | Đã Paid, bất kỳ thay đổi nào có căn cứ | Delta kỳ sau, không sửa kỳ gốc |

**GAP:** \`VNLeaveLedgerEntry\` hiện chỉ tạo các giao dịch tăng/giảm độc lập, chưa tự kết nối \`LeaveRequest\` hoặc \`AvailableLeave\`. Code chặn sửa/xóa trên instance; bulk/raw SQL cần kiểm soát ở lớp dịch vụ/DB.

## 7. WF-PAY-RULE — Bộ công thức có version
| Từ → Đến | Action/actor | Guard | Side effect |
|---|---|---|---|
| None → draft | Superuser create [CODE] | Company, code, version, effective_from | RuleSet Draft |
| draft → review | Superuser submit [CODE] | Có ít nhất một dòng, biểu thức hợp lệ | Khóa chỉnh rules ngoài Draft |
| review → draft | Superuser return [CODE] | Đúng trạng thái | Cho sửa config, audit |
| review → approved | Checker khác maker [CODE] | Legal ref, approved actor/time, dependency valid, Golden Cases match, không trùng ngày hiệu lực | Đã duyệt, immutable |
| approved → retired | Superuser [CODE model] | Chỉ transition này được phép; giữ lịch sử | Admin method có nhưng **chưa đăng ký trong actions**, cần sửa |
| approved → rule active for pay date | Payroll resolver [CODE service, chưa gắn batch] | Company/code/as_of, đúng một effective candidate hợp lệ | Chọn bản được duyệt theo hiệu lực |
| retired → edited | Không cho phép [CODE] | Bất biến | \`INVALID_STATE_TRANSITION\` |

**Rủi ro policy:** phiên bản ngắn hạn hết hiệu lực có thể khiến resolver dùng lại bản cũ đang còn hiệu lực; cần quy định rõ priority, khoảng hiệu lực, ngày chính sách thay thế và tình huống không có rule.

## 8. WF-PAY — Kỳ lương, phiếu lương, chi trả [SPEC]
| Từ → Đến | Actor/action | Guard bắt buộc | Side effect |
|---|---|---|---|
| None → Draft | Payroll create | company/period/pay_date; locked attendance; HĐ/rule approved; idempotency | Tạo run + snapshot source hash |
| Draft → Calculated | Payroll calculate | Rule version, input schema, không thiếu dữ liệu | Tạo paylines gross, BH NLĐ/DN, tax, net |
| Calculated → Reconciled | Payroll reconcile | Tổng các dòng bằng gross/net, ngoại lệ đóng | Báo cáo sai lệch kỳ trước |
| Reconciled → Review | Maker submit | Không còn BLOCKED; snapshot hash nguyên vẹn | Lưu signer/version |
| Review → Approved | Pay Approver | Different maker/checker, đúng pháp nhân; nguồn không thay đổi | Freeze payslips |
| Approved → PaymentPending | Finance export | Đã kiểm tra beneficiary, checksum, double export control | File ngân hàng, chỉ Pending |
| PaymentPending → PartiallyPaid | Finance reconcile | Một phần giao dịch bank matched | Paid per-employee, batch chưa hoàn tất |
| PaymentPending/PartiallyPaid → Paid | Finance reconcile | Tất cả dòng cần thanh toán có acknowledgment và amount match | Paid terminal; khóa số đã chi |
| Draft/Review → Cancelled | Authorized user | Chưa Paid, lý do/permission, không che lịch sử | Event cancelled |
| Paid → AdjustmentCreated | Payroll [new period] | Có thay đổi hợp lệ, delta/approval | Không sửa bản Paid |

**Giới hạn:** \`vn_payroll.preview_ruleset()\` chỉ tính thử RuleSet với JSON, không ghi \`Payslip\`, không tích hợp \`payroll_run.py\`. WF-PAY trên là mục tiêu, không ghi là trạng thái triển khai.

## 9. WF-OFF — Nghỉ việc, bàn giao và quyền truy cập [SPEC]
| Từ → Đến | Action | Guard | Kết quả |
|---|---|---|---|
| Initiated → Reviewed | HR/legal | Loại chấm dứt, căn cứ, ngày, báo trước theo trường hợp | Decision file |
| Reviewed → Handover | Manager/HR | Danh sách tài sản, nghĩa vụ, công việc, dữ liệu | Checklist |
| Handover → FinalSettlement | Payroll/Finance | Chốt công, phép, thuế/BH, công nợ, payslip | Settlement có chứng cứ |
| FinalSettlement → Completed | HR/IT | Revocation có xác nhận, thanh toán/chứng từ theo policy | Employee offboarded, retention active |
| Completed → Archived | Records officer | Retention/căn cứ xử lý, legal hold | Archive immutable |

## 10. Nhánh lỗi chung, retry và bù trừ
| Tình huống | Response/UI | Recovery |
|---|---|---|
| Duplicate submit/approve | \`DUPLICATE_REQUEST\` hoặc trả kết quả lần đầu nếu cùng idempotency key | No duplicate ledger/payroll |
| Stale revision / phê duyệt đồng thời | HTTP 409 \`STATE_CONFLICT\` | Refresh record và quyết định lại, không overwrite |
| Không có quyền/khác pháp nhân | HTTP 403/404 \`TENANT_SCOPE_DENIED\` | Không tiết lộ đối tượng; audit security |
| Thiếu cấu hình rule hiệu lực | HTTP 422 \`RULE_NOT_EFFECTIVE\` | Chặn action chính thức, đưa vào policy decision |
| Kỳ công đã Locked | HTTP 409 \`PERIOD_LOCKED\` | Yêu cầu reopen/delta, không sửa DB trực tiếp |
| Payslip đã Paid | HTTP 409 \`PAID_IMMUTABLE\` | Tạo correction riêng ở kỳ sau |
| Downstream failure sau DB commit | Hiển thị PendingSync, mã correlation | Outbox retry idempotent, reconciliation không cho giả hoàn tất |
| Bị từ chối | Reason code và text tiếng Việt | Cho sửa Draft mới khi policy cho phép |

## 11. Checklist kiểm thử state machine
- Mỗi cạnh hợp lệ 1 TC positive; mỗi cạnh không hợp lệ 1 TC negative; thao tác cùng request 2 lần 1 TC idempotency.
- Thử actor sai vai trò, sai pháp nhân, token hết hạn, ủy quyền hết hiệu lực, reviewer=creator.
- Thử chuyển trạng thái khi dữ liệu thay đổi giữa read và commit, 2 browser duyệt đồng thời, DB rollback.
- Thử ngày 31/12→01/01, ca qua đêm, điều chuyển giữa tháng, người phụ thuộc thay đổi hiệu lực, RuleSet supersession.
- Thử hệ thống downstream ngừng hoạt động sau commit và sau gửi event; không được nhân đôi tiền/số dư.
- Mọi action chuyển trạng thái ghi audit; riêng thao tác đọc/xuất PII ghi sensitive access log.

Tham chiếu [SRS](02-SRS-USE-CASE-VA-BUSINESS-RULE.md), [23 UC](12-USE-CASE-DETAILS.md), [Validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [UAT](15-TRACEABILITY-UAT-MATRIX.md).
