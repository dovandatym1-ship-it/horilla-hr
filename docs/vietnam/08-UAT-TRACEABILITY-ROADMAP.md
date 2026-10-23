# Kế hoạch triển khai, ma trận truy vết và kiểm thử UAT
**Mã:** VNHRM-DEL-08 · **Phiên bản:** 1.0 · **Trạng thái:** Planning/TO-BE · **Ngày:** 17/10/2026

## 1. Phân kỳ triển khai
| Giai đoạn | Thời gian ước tính | Phụ thuộc | Điều kiện hoàn thành |
|---|---|---|---|
| P0 - Baseline | Tuần 1–2 | Horilla 2.0, dữ liệu thử nghiệm | Chạy Docker/migration/tests và báo cáo baseline |
| P1 - Tiếng Việt | Tuần 3–4 | Thuật ngữ và Design System | vi locale, template, PDF/Excel, VND, timezone |
| P2 - Hồ sơ/HĐ | Tuần 5–7 | Data Dictionary và xác nhận quy chế | Legal profile, dependent, amendment, lịch sử |
| P3 - Công/Phép | Tuần 8–10 | Lịch/ca/rule OT & phép được ký duyệt | Chốt công, ledger phép, reconcile |
| P4 - Lương | Tuần 11–16 | Căn cứ pháp lý và golden case đã ký duyệt | Payroll adapter VN, tax, insurance, immutable Paid |
| P5 - Báo cáo | Tuần 17–18 | Công/lương đối soát | Báo cáo, xuất ngân hàng, kiểm soát quyền |
| P6 - UAT/Pilot | Tuần 19–20 | End-to-end regression | UAT ký duyệt, backup/restore, SOP/rollback |

Ước tính này giả định 2 backend, 1 frontend, 1 QA, 1 BA/PM, có hỗ trợ thường xuyên của HR, Payroll, Pháp chế. Không được dùng ước tính làm cam kết khi chưa chạy baseline.

## 2. Backlog theo ID và source mapping
| Feature | Phần cần làm | Mã nguồn tiếp cận đầu tiên | Test |
|---|---|---|---|
| F-VN-001 | Cài/chạy baseline | docker-compose.yml, requirements.txt, tests/ | TC-NFR-001 |
| F-VN-002 | Tiếng Việt hoàn chỉnh | horilla/settings/base.py, horilla/locale, templates | TC-I18N-001 |
| F-VN-003 | VND và ngày giờ | settings, payroll/context_processors.py, export | TC-I18N-002 |
| F-VN-004 | Pháp nhân/vùng | base/models.py: Company, Department | TC-ORG-001/002 |
| F-VN-005 | Định danh | employee/models.py | TC-EMP-001/002 |
| F-VN-006 | Người phụ thuộc | vn_hrm TO-BE, employee/models.py | TC-PIT-002 |
| F-VN-007 | HĐ/phụ lục | payroll/models/models.py: Contract | TC-CON-001/002 |
| F-VN-008 | Công | attendance/models.py, base/models.py | TC-ATT-001…005 |
| F-VN-009 | OT | payroll/methods/payslip_calc.py | TC-OT-001…003 |
| F-VN-010 | Nghỉ | leave/models.py, leave/services.py | TC-LEV-001…006 |
| F-VN-011 | Rule version | vn_payroll TO-BE, payroll/tax_packs.py | TC-PAY-004 |
| F-VN-012 | Gross/Net | payroll/methods/payroll_run.py, payslip_calc.py | TC-PAY-002 |
| F-VN-013 | Bảo hiểm | payroll/methods/contributions.py | TC-INS-001/002 |
| F-VN-014 | PIT | payroll/methods/tax_calc.py | TC-PIT-001…003 |
| F-VN-015 | Khóa kỳ | payroll/models/payroll_batch.py | TC-PAY-003 |
| F-VN-016 | Báo cáo | report/registry.py, report/export.py | TC-RPT-001…003 |
| F-VN-017 | Bank export | vn_reports TO-BE | TC-RPT-004 |
| F-VN-018 | PII & RBAC | horilla_auth, horilla_audit | TC-SEC-001…008 |
| F-VN-019 | Regression | horilla_api/authentication.py, tests | CI gate |
| F-VN-020 | Pilot | toàn chuỗi | UAT signoff |

## 3. Bộ UAT chi tiết tăng cường
| TC | Thiết lập | Kỳ vọng kiểm chứng |
|---|---|---|
| TC-I18N-001 | Chuyển vi/en, mở menu/form/notification | Ngôn ngữ nhất quán, không mất key, không lỗi dấu |
| TC-I18N-002 | Nhập 17/10/2026 và VND, xuất PDF/Excel/API | Ngày và tiền đúng trên các kênh, UTC không bị đổi |
| TC-ORG-001 | Cùng tên đơn vị ở 2 công ty | Không trộn nhân sự |
| TC-ORG-002 | Địa chỉ trước/sau thay đổi địa giới | Giữ bản cũ và vùng lương theo hiệu lực |
| TC-EMP-001 | CCCD thiếu có lý do | Chấp nhận theo status cần bổ sung, không giả dữ liệu |
| TC-EMP-002 | User không quyền xem CCCD | Mask đúng cả API/report |
| TC-EMP-003 | Hai hồ sơ trùng định danh | Cảnh báo, workflow đối soát, không tự gộp |
| TC-CON-001 | Sửa lương giữa tháng | Prorate theo hợp đồng effective date |
| TC-CON-002 | Hai HĐ chồng khoảng hiệu lực trái policy | Block, nêu nguyên nhân |
| TC-CON-004 | Điều chỉnh HĐ sau Paid | Lập delta, không sửa phiếu cũ |
| TC-PAY-008 | Taxable income 10;10,01;30;30,01;60;100;100,01 triệu | Chọn đúng bậc PIT 2026; làm tròn theo policy |
| TC-PAY-009 | Phụ cấp chịu/không chịu thuế/BH độc lập | Không gộp 2 thuộc tính pháp lý |
| TC-PAY-010 | Kỳ cũ dùng rule version A, kỳ mới B | Recompute snapshot kỳ cũ vẫn A |
| TC-PAY-011 | Retry tạo batch cùng idempotency key | Không sinh payslip đôi |
| TC-PAY-012 | Người không cư trú | Không dùng công thức người cư trú mặc định |
| TC-PAY-013 | Nghỉ việc giữa kỳ | Chỉ tính theo điều kiện công, HĐ và khoản phát sinh hợp lệ |
| TC-RPT-001 | Bảng lương 500 NV | Tổng số tiền các dòng bằng tổng report |
| TC-RPT-002 | Dữ liệu có ký tự Unicode, công thức đầu ô | Không lỗi dấu, không CSV injection |
| TC-RPT-003 | Manager phòng A báo cáo phòng B | Không lộ dữ liệu |
| TC-RPT-004 | File bank thiếu một giao dịch | Báo lệch, không tự chuyển Paid toàn bộ |
| TC-NFR-001 | Backup DB+media, restore | Số bản ghi, chứng từ và checksum đúng |
| TC-NFR-002 | Dataset 100/500/1.000 người có công+phép+lương | Benchmark ghi CPU/time/error; SLO chốt sau P0 |

Các TC còn lại về công/OT/phép nằm ở tài liệu OPS-04; các TC thuế/bảo hiểm tại PAY-05; TC an toàn tại SEC-07. **Không đánh dấu PASS khi chưa chạy thật.**

## 4. Quality Gates
**G0:** có baseline/test run ghi thời điểm và commit SHA. **G1:** i18n/data migration pass. **G2:** công, OT, nghỉ và ledger đối soát. **G3:** bộ kiểm thử golden payroll bằng Excel/Oracle độc lập của Kế toán; không còn quyết định pháp lý critical mở. **G4:** không có lỗi IDOR/tenant/field leak; security review. **G5:** HR/Payroll/Finance ký UAT; restore/rollback thành công; vận hành thử có giám sát.

## 5. Definition of Ready và Done
**DoR:** yêu cầu có BR/UC, actor, pre/postconditions, field-level validation, permission scope, policy/effective-date và test case; mọi mục chưa rõ ghi OPEN/BLOCKED. **DoD:** migration có rollback, test unit/integration/E2E, không hồi quy upstream, màn hình tiếng Việt, log, bảo vệ dữ liệu và UAT có bằng chứng; không còn lỗi nghiêm trọng chưa được chấp thuận.

## 6. Thứ tự PR triển khai sau khi duyệt tài liệu
1. feature/vn-i18n-foundation — locale, timezone, format, PDF/Excel fonts.
2. feature/vn-employee-legal — pháp nhân, hồ sơ pháp lý, người phụ thuộc và migration.
3. feature/vn-contract — HĐ, phụ lục, effective dating.
4. feature/vn-attendance-leave — ca, chốt công, phép ledger.
5. feature/vn-payroll — rules tax/BH, Decimal adapter, snapshots, golden tests.
6. feature/vn-reports — báo cáo, bank export, audit, tenant scoping.

Tất cả PR code chạy qua review và CI; không force-push lên 2.0, không merge âm thầm. Sau khi cập nhật upstream phải kiểm tra migration và contract/API compatibility.


## 7. Phụ lục UAT v1.1 — Traceability và tiêu chí PASS
Các testcase mục 3 ở trên là danh mục ban đầu. [MATRIX-15](15-TRACEABILITY-UAT-MATRIX.md) là bảng bổ sung liên kết đầy đủ 23 UC với validation, workflow, mã lỗi, testcase biên, trùng, đồng thời, pháp nhân và bằng chứng. Mỗi test phải có branch/commit SHA, dữ liệu synthetic, expected độc lập, kết quả thực, ảnh/log che nhạy cảm, reviewer và trạng thái.

**Current execution status:** tất cả TC mới ghi **DESIGNED / NOT RUN**; không công bố Django runtime/CI/UAT đã PASS khi chưa chạy. Phần model code PR #3 chỉ đánh CODE_STATIC_ONLY. **DoR:** UC+BR+DE+WF+permission+error+TC+policy owner rõ; **DoD:** test từng mức/unit/integration/E2E + migration + UAT có evidence, policy legal chốt và không tồn tại GAP P0 chưa đóng.
