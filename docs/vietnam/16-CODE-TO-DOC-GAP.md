# VN-HRM | Đối chiếu tài liệu SRS/BRD/UC với mã nguồn
**ID:** VNHRM-GAP-16 · **Phiên bản:** 1.1 · **Ngày:** 18/10/2026 · **Căn cứ:** \`feature/vietnam-hrm-foundation\` (PR #1), \`feature/vn-i18n-foundation\` (PR #2), \`feature/vn-dynamic-hrm\` (PR #3). **Chỉ code review tĩnh, không có bằng chứng CI runtime/UAT PASS.**

## 1. Baseline và trạng thái
| Hạng mục | Nguồn | Xác nhận | Không được suy diễn |
|---|---|---|---|
| Bộ BRD/SRS/UC/DE tiếng Việt | PR #1, docs/vietnam | Documentation TO-BE, chưa merge 2.0 | Đã được HR/Finance ký duyệt hoặc được code triển khai |
| Locale tiếng Việt, VND và timezone | PR #2, code locale/settings | Có code i18n và unit tests được thêm | Toàn bộ UI/PDF/Excel đã Việt hóa hoặc kiểm thử PASS |
| Hồ sơ VN/legal/dependent/amendment/correction/ledger | PR #3, vn_hrm/models.py và admin.py | Có bảng model/validator và Admin superuser | Đã có workflow HR staff, kết nối tự động Horilla lõi |
| Công thức động, preview, Golden Cases | PR #3, vn_payroll/* | Có evaluator Decimal/AST và RuleSet/Admin | Đã ghi phiếu lương, tính luật 2026 chuẩn hoặc có golden sign-off |
| Main branch 2.0 | repository default | Không chứa PR #1/#2/#3 khi chưa merge | Có thể chạy tính năng VN trực tiếp trên 2.0 |

## 2. Mismatch và missing requirement quan trọng
| GAP ID | Priority | Evidence code ↔ tài liệu | Hành động để đóng GAP | Tiêu chí chấp nhận |
|---|---|---|---|---|
| GAP-001 | P0 | SRS payroll E2E có phát hành/đối soát/Paid, nhưng \`vn_payroll.services.preview_ruleset\` không ghi Payslip, \`payroll_run.py\` chưa nối adapter | Thiết kế input snapshot, rule resolver, schema payline, reconciliation và roll-forward/rollback; mapping từng field | TC-PAY-001..013 và golden independent PASS |
| GAP-002 | P0 | SRS duyệt nghỉ ghi phép, code \`VNLeaveLedgerEntry\` độc lập \`AvailableLeave\`/\`LeaveRequest\` | Service transaction + idempotency + nguồn lịch + bút toán đảo và lock | TC-LED-001..006, TC-LEV-002 PASS |
| GAP-003 | P0 | UC sửa công phải giữ raw + áp công mới; code \`VNAttendanceCorrection\` chỉ trạng thái, chưa link source/Attendance, chưa company cross-check trong clean | Thêm source reference, before/after, evidence, policy lock, adapter Attendance & audit | TC-COR-004..007 PASS |
| GAP-004 | P0 | SRS/PAY yêu cầu tenant/field RBAC, Admin mới chỉ superuser, không có HR UI tenant-scoped | Thiết kế grant policy, row/field filtering cho CRUD/search/export/preview | TC-SEC-001..008 PASS |
| GAP-005 | P1 | SRS phụ lục approved phải áp mức lương, model \`VNContractAmendment\` chưa cập nhật \`Contract.wage\` | Event + version hợp đồng, ngày hiệu lực, prorate/recalculation | TC-CON-001/004/009 PASS |
| GAP-006 | P1 | Data Dictionary dùng \`Dependent.relationship_code\` enum nhưng code \`VNDependent.relationship\` free-text Char(40) | Danh mục quan hệ có version/mapping legacy hoặc chuẩn hóa logic đã duyệt | TC-DEP-003 PASS |
| GAP-007 | P1 | \`VNEmployeeLegalProfile\` có trạng thái verified nhưng thiếu verifier/evidence/effective history trong model mới | Xác minh maker-checker, sự kiện đổi trạng thái, chứng cứ có quyền | TC-EMP-001/002, TC-DEP-004 PASS |
| GAP-008 | P1 | \`VNDependent\` cho khoảng hiệu lực nhưng thiếu loại nhóm/kiểm tra trùng chồng lấn/hồ sơ eligible độc lập | Quy tắc duplicate và eligibility version; không auto PIT khi chưa verify | TC-DEP-005, TC-PIT-002/003 PASS |
| GAP-009 | P1 | \`VNContractAmendment.new_monthly_wage_vnd\` chỉ chống âm; chưa đối chiếu minimum wage theo vùng/effective location | Rule evaluator pháp lý theo thời gian và nhóm lao động | TC-CON-003/007 PASS |
| GAP-010 | P1 | \`VNAttendanceCorrection.requested_minutes\` -1440..1440, nhưng SRS chưa định nghĩa delta/total, ngày ca và ranh giới | Định nghĩa chính xác ý nghĩa, min/max theo loại ca, cách tính giờ | TC-COR-001/002 PASS + HR sign-off |
| GAP-011 | P1 | \`VNLeaveLedgerEntry.units\` Decimal(9,2) !=0; không có chuẩn ngày/giờ/số dư âm, chống sửa bằng instance nhưng bulk SQL bypass được | Policy unit + closed-period guard + access service/DB constraints | TC-LED-003..006 PASS |
| GAP-012 | P1 | \`VNRuleSet\` hỗ trợ effective dates nhưng thứ tự ưu tiên giữa nhiều version ngắn hạn chưa rõ; code chọn effective_from gần nhất | Policy supersession/retirement; test gap/overlap/hồi tố | TC-RULE-008/010 + case effective_to PASS |
| GAP-013 | P2 | \`VNRuleSetAdmin.retire_approved()\` định nghĩa nhưng không có trong danh sách actions được đăng ký | Thêm action có guard và test | TC-RULE-010 PASS |
| GAP-014 | P1 | BRD payroll đề cập tax/BH theo hiệu lực nhưng \`vn_payroll\` chưa có pack được HR/Kế toán/Pháp chế phê duyệt và source trace | Decision Log nguồn pháp lý, golden cases từng nhóm, hiệu lực & rounding | G3 độc lập PASS |
| GAP-015 | P1 | \`VNEmployeeLegalProfile\` chỉ lưu suffix/vault_ref, chưa có vault tích hợp, audit đọc/xuất field | Adapter bảo mật, secret boundary, object ACL, PII event log | TC-SEC-002/004/007/008 PASS |
| GAP-016 | P1 | BRD workflow trạng thái To-Be khác với model Horilla và hai trạng thái amendment | Mapping enum/transition cho từng object và UI action | WF tables được review + negative TC PASS |
| GAP-017 | P2 | SRS nguyên bản liệt kê UC nhưng thiếu per-field validation & ALT; nay docs 10–15 bổ sung đặc tả, chưa sign-off | Review từng field, resolve decisions, tạo Jira/issue; cập nhật API/schema | DoR field/UC đạt, reviewer ký |
| GAP-018 | P2 | PR #2 chỉ 294 msgid vi, chưa xác minh full UI/notification/report/PDF/i18n import | Inventory tất cả string; compile/run/browser smoke; test unicode/print | TC-I18N-001/002 và TC-UI PASS |
| GAP-019 | P1 | Merge lineage: PR #3 base PR #2, PR #1 tách độc lập; code và doc chưa cùng baseline | Merge theo review order rồi reconcile conflicts; trace SHA/schema từ cuối | Branch integration build/CI/UAT PASS |
| GAP-020 | P1 | Check logic mới chủ yếu \`clean()/save()\`; các đường \`QuerySet.update()\`, \`bulk_create()\`, import, job có thể không gọi full_clean | Central service APIs, serializer validation, DB constraints, audited commands | Negative tests cho tất cả entry points PASS |

## 3. Bảng hợp đồng dữ liệu cần thống nhất giữa BRD, SRS, code
| Khái niệm | Tên trong tài liệu TO-BE | Field code PR #3 | Quyết định |
|---|---|---|---|
| Định danh cá nhân | EmployeeIdentity.citizen_id encrypted | VNEmployeeLegalProfile.citizen_id_suffix / citizen_id_vault_ref | Không mô tả raw CCCD tồn tại trong bảng VN mới; chờ vault |
| Cư trú tính thuế | TaxResidency.status với ngày hiệu lực | VNEmployeeLegalProfile.residency_type; chưa có valid_from/to | Cần version, căn cứ và reviewer |
| Người phụ thuộc | Dependent.relationship_code enum, eligibility history | VNDependent.relationship text, eligible_from/to, verification_status | Cần chuẩn danh mục + lịch sử eligibility |
| Phụ lục lương | ContractAmendment hiệu lực/apply | VNContractAmendment approved, new_monthly_wage_vnd | Chưa thay Contract.wage; adapter riêng |
| Sửa công | VNAttendanceDecision với source log | VNAttendanceCorrection.work_date, requested_minutes, status | Chưa đủ trace before/after/source |
| Sổ phép | VNLeaveLedger/AvailableLeave | VNLeaveLedgerEntry company/source_key/units | Chưa đồng bộ LeaveRequest và AvailableLeave |
| Quy tắc lương | LegalRuleVersion, RuleSet version | VNRuleSet / VNPayRule | Có config/evaluator, thiếu payroll snapshot adapter |
| Snapshot | PayRunSnapshot source_hash, Payslip rule_version | Chưa có model mới tương ứng trong PR #3 | Không khẳng định Paid immutable đã được bảo vệ end-to-end |
| Phân quyền | DataScopeGrant/SensitiveAccessLog | Django Admin superuser restriction | Chưa có tenant-aware HR/Payroll UI cho module VN |

## 4. Quyết định nghiệp vụ còn mở — không hardcode khi chưa chốt
| Decision | Chủ quyết định | Nội dung phải chốt | Ảnh hưởng |
|---|---|---|---|
| DEC-VN-ORG-01 | HR/Security | Mã NV unique toàn hệ thống hay theo pháp nhân; quy tắc điều chuyển | Employee, API, import |
| DEC-VN-ID-01 | DPO/Pháp chế/HR | Kho vault, quy tắc xử lý trùng CCCD/MST/BHXH, lưu/xóa/tra cứu | Legal profile |
| DEC-VN-DEP-01 | Payroll/Pháp chế | Nhóm người phụ thuộc, verification, thời điểm đủ điều kiện PIT | Dependent, PIT |
| DEC-VN-CON-01 | HR/Pháp chế | HĐ song song, rule lương tối thiểu, ưu tiên phụ lục và hồi tố | Contract, Payroll |
| DEC-VN-ATT-01 | HR | requested_minutes là delta hay tổng; cửa sổ ca, timezone, reopen | Attendance |
| DEC-VN-OT-01 | HR/Pháp chế | OT giới hạn, ranh giới ngày, ưu tiên ngày lễ/đêm, nghỉ giữa ca | OT, Payroll |
| DEC-VN-LEV-01 | HR/Pháp chế | Đơn vị phép, prorate, carryforward, entitlement, hồi tố | Leave, ledger |
| DEC-VN-PAY-01 | Payroll/Pháp chế | Basis BH, PIT, rounding, tax recognition date, gross/net, rule priority | RuleSet, Payslip |
| DEC-VN-PAY-02 | Finance | Batch partial payment, bank ref, paid lock, adjustment | Banking |
| DEC-VN-SEC-01 | Security/HR | Maker/checker delegation, field grants, separation infra vs payroll | RBAC, audit |
| DEC-VN-OPS-01 | PM/Tech Lead | Cutover/migration, rollback, retaining legacy Horilla compatibility | Release |

## 5. Quy trình đóng GAP
1. BA gán owner, bằng chứng hiện tại, UC/BR/DE, mức ảnh hưởng P0–P2 và decision liên quan.
2. Người sở hữu policy xác định quy tắc có căn cứ, hiệu lực và exception; nếu chưa quyết được đánh dấu BLOCKED_BY_POLICY.
3. Architect so mapping model/API + migration; Dev triển khai ở PR nhỏ, không sửa lịch sử Paid hoặc schema lõi thiếu strategy.
4. QA viết positive/negative/boundary/concurrency tests và chạy. Chỉ đánh PASS khi có commit SHA, runtime, fixtures, số liệu expected độc lập.
5. HR/Finance/Security/Pháp chế ký UAT theo phạm vi; BA cập nhật trạng thái \`IMPLEMENTED_TESTED\` và link bằng chứng.

## 6. Cảnh báo merge và vận hành
Không tự merge PR #1 vào 2.0 nếu chưa review; không đưa PR #3 vào production trước khi PR #2 đã sẵn sàng và kiểm tra migrations/tests. Nội dung tài liệu này không thay đổi code, chỉ ghi nhận và làm rõ GAP để lên backlog. Mọi tài liệu luật nội bộ ở \`05\`/\`06\` phải được rà soát hiệu lực tại kỳ áp dụng trước khi dùng tham số tính lương thực.

Tham chiếu [23 UC](12-USE-CASE-DETAILS.md), [Field validation](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [State machines](13-WORKFLOW-STATE-TRANSITIONS.md), [Tests](15-TRACEABILITY-UAT-MATRIX.md).
