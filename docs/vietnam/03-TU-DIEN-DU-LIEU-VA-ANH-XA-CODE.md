# VN-HRM | Từ điển dữ liệu, mô hình logic và ánh xạ code Horilla
**Mã:** VNHRM-DATA-03 · **Phiên bản:** 1.0 · **Ngày:** 17/10/2026 · **Trạng thái:** TO-BE/Dự thảo; không phải Django migration.

## 1. Nguyên tắc dữ liệu
- Không thay khóa `Employee.id`, `Company.id`, `Contract.id` đang có bằng CCCD/MST; dùng khóa quan hệ ổn định và mã nghiệp vụ độc lập.
- Tách **trạng thái hiện tại** và **lịch sử hiệu lực**; mọi thay đổi pháp nhân, phòng ban, hợp đồng, tham gia BH, người phụ thuộc, mức lương phải truy được `valid_from`/`valid_to`.
- Phân biệt ba thời gian: `occurred_at` (sự kiện thực tế), `effective_at` (áp dụng nghiệp vụ), `recorded_at` (hệ thống ghi nhận). Định danh sự kiện duy nhất và nguồn xuất xứ.
- Dữ liệu tiền là VND nguyên hoặc `Decimal` theo chính sách; không dùng `float` cho phép cộng/trừ số tiền chính thức trong adapter Việt Nam.
- Dữ liệu cá nhân nhạy cảm được che/mã hóa theo chính sách và có audit trên thao tác đọc/xuất; phân quyền cột (field) và bản ghi (row).
- Giữ idempotency khi nhập liệu, thiết bị gửi lại log, xử lý đơn và chạy bảng lương; mọi migration có kế hoạch giữ nguyên dữ liệu, rollback và truy vết.

## 2. Ánh xạ model AS-IS → dữ liệu TO-BE
| Miền | Model/đường dẫn Horilla đã xác nhận | Đề xuất mở rộng | Khuyến nghị |
|---|---|---|---|
| Công ty | `base.models.Company` | `VNLegalEntityProfile`, `VNWorkLocation` | OneToOne/FK, không phá model lõi |
| Bộ phận/ca | `Department`, `EmployeeShift`, `Roster` | `VNShiftPolicyVersion`, `VNWorkCalendar` | Ngày hiệu lực, địa điểm, loại ca |
| Cá nhân | `employee.models.Employee` | `VNEmployeeIdentity`, `VNResidencyStatus` | CCCD/MST/BHXH riêng; liên kết bằng FK |
| Công việc | `EmployeeWorkInformation` | `VNEmploymentAssignment` | Pháp nhân, đơn vị, điểm làm việc theo thời gian |
| Ngân hàng | `EmployeeBankDetails` | `VNBankPayoutProfile` | Kiểm tra tên chủ TK/đồng tiền/file bank |
| Hợp đồng | `payroll.models.models.Contract` | `VNContractTerms`, `VNContractAmendment` | Loại HĐ, thử việc, phụ lục, hiệu lực |
| Người phụ thuộc | `Employee.children` chỉ là số con | `VNDependent`, `VNDependentEligibility` | Không suy quyền giảm trừ từ số con |
| Công | `attendance.models.Attendance` | `VNRawAttendanceEvent`, `VNAttendanceDecision` | Giữ sự kiện gốc và quyết định sửa |
| OT | `AttendanceOverTime` và các phép tính trong `payslip_calc.py` | `VNOvertimeRequest`, `VNOvertimeClassification` | Mã loại OT, giờ duyệt, căn cứ |
| Nghỉ | `leave.models.LeaveType, AvailableLeave, LeaveRequest` | `VNLeavePolicyVersion`, `VNLeaveLedger` | Không xóa số dư/hạch toán lịch sử |
| Kỳ lương | `payroll.models.payroll_batch.PayrollBatch` | `VNPayrollPolicySnapshot`, `VNPayrollReconciliation` | Tên kỳ, khóa công, rule version |
| Phiếu lương | `payroll.models.models.Payslip` | `VNPaylineTrace`, `VNPayrollAdjustment` | Chi tiết thành phần bất biến |
| Thuế | `FilingStatus`, `TaxBracket` | `VNPersonalTaxProfile`, `VNLegalRule` | Đặc thù cư trú và kỳ thuế |
| BH | `Deduction`, `contributions.py` | `VNSocialInsuranceEnrollment`, `VNContributionSnapshot` | NLĐ/DN tách và lịch sử thay đổi |
| Phân quyền | `horilla_auth` và `TenantScopedJWTAuthentication` | `VNDataScopeGrant`, `VNSensitiveAccessLog` | Role + scope + policy riêng từng field |

## 3. Data Dictionary mức logic (TO-BE)
Mỗi mã DE là một khái niệm bắt buộc chuẩn hóa, không đồng nghĩa cần thêm ngay cột trên model hiện có. **PK**: khóa chính; **FK**: khóa ngoài; **S**: nhạy cảm; **R**: bắt buộc; **U**: duy nhất theo phạm vi; **H**: lưu lịch sử.

| DE | Entity.field | Kiểu/điều kiện | Bảo vệ / rule |
|---|---|---|---|
| DE-VN-ORG-001 | LegalEntity.code | varchar(32), R,U | Không tái sử dụng |
| DE-VN-ORG-002 | LegalEntity.tax_id | varchar(30), có kiểm tra theo quy chế | S; chỉ nhóm quản lý xem đủ |
| DE-VN-ORG-003 | LegalEntity.legal_name | nvarchar(255), R | Unicode NFC |
| DE-VN-ORG-004 | WorkLocation.province_code | varchar(20), R | FK mã địa giới có version |
| DE-VN-ORG-005 | WorkLocation.commune_code | varchar(20), R | FK mã xã/phường/đặc khu |
| DE-VN-ORG-006 | WorkLocation.minimum_wage_zone | enum/lookup, H | Phụ thuộc hiệu lực địa bàn |
| DE-VN-EMP-001 | Employee.staff_code | varchar(50), R,U | Không dùng làm PK DB |
| DE-VN-EMP-002 | EmployeeIdentity.citizen_id | encrypted varchar, U sau chuẩn hóa | S; mask, audit, chỉ đọc theo quyền |
| DE-VN-EMP-003 | EmployeeIdentity.citizen_id_issued_at | date | S, optional; xác thực quy tắc |
| DE-VN-EMP-004 | EmployeeIdentity.citizen_id_issued_by | nvarchar(255) | Không ép hardcode cơ quan |
| DE-VN-EMP-005 | EmployeeIdentity.tax_identifier | varchar, H | S; không dùng số trôi nổi |
| DE-VN-EMP-006 | EmployeeIdentity.social_insurance_id | varchar, H | S; dữ liệu kỳ BH |
| DE-VN-EMP-007 | EmployeeIdentity.nationality | ISO code | Đối tượng/nhóm lao động |
| DE-VN-EMP-008 | TaxResidency.status | enum, H | Xác nhận bởi payroll, hiệu lực |
| DE-VN-EMP-009 | EmploymentAssignment.company_id | FK, H, R | Pháp nhân sở hữu hồ sơ |
| DE-VN-EMP-010 | EmploymentAssignment.work_location_id | FK, H | Căn cứ lịch/địa điểm |
| DE-VN-EMP-011 | EmploymentAssignment.valid_from/to | date range | Không overlap trái policy |
| DE-VN-EMP-012 | BankProfile.account_number | encrypted varchar | S; không đưa full vào log |
| DE-VN-DEP-001 | Dependent.employee_id | FK, R | Chỉ HR/Payroll có quyền |
| DE-VN-DEP-002 | Dependent.relationship_code | enum/lookup | Không suy từ employee.children |
| DE-VN-DEP-003 | Dependent.identity_identifier | encrypted varchar | S; che/mã hóa |
| DE-VN-DEP-004 | DependentEligibility.valid_from/to | date range, H | Xác định kỳ giảm trừ |
| DE-VN-DEP-005 | DependentEligibility.verification_status | enum, H | Cần quy trình xác thực |
| DE-VN-CON-001 | ContractTerm.contract_id | FK, R | 1 phiên bản gắn HĐ gốc |
| DE-VN-CON-002 | ContractTerm.contract_type | enum | HĐ có/không thời hạn, khác |
| DE-VN-CON-003 | ContractTerm.probation_from/to | date nullable | Không mặc định mọi NV đều thử việc |
| DE-VN-CON-004 | ContractTerm.salary_amount | Decimal/Int VND | S, H, không dùng float ở lớp mới |
| DE-VN-CON-005 | ContractTerm.insurance_salary_basis | Decimal/Int, H | Có căn cứ & sự kiện thay đổi |
| DE-VN-ATT-001 | RawAttendance.external_event_id | varchar, U theo source | Idempotency |
| DE-VN-ATT-002 | RawAttendance.happened_at_utc | tz datetime, R | Bảo toàn nguồn & timezone |
| DE-VN-ATT-003 | RawAttendance.device_id/source | varchar, R | Kiểm định điểm nguồn |
| DE-VN-ATT-004 | AttendanceDecision.work_date | date theo ca | Không tự suy theo 00:00 |
| DE-VN-ATT-005 | AttendanceDecision.approved_ot_minutes | int >=0 | Chỉ giờ đã duyệt |
| DE-VN-ATT-006 | AttendanceDecision.status/reason | enum/text, H | Không thay bản ghi gốc |
| DE-VN-LEV-001 | LeaveLedger.event_id | UUID, U | Chống debit/credit trùng |
| DE-VN-LEV-002 | LeaveLedger.units | Decimal | Đơn vị ngày hoặc giờ rõ ràng |
| DE-VN-LEV-003 | LeaveLedger.source_request_id | FK | Đối chiếu được từng đơn |
| DE-VN-PAY-001 | RuleSet.rule_code | varchar(64), R | Legal ref + phê duyệt |
| DE-VN-PAY-002 | RuleSet.effective_from/to | date range | H, không overlap cùng ưu tiên |
| DE-VN-PAY-003 | PayRunSnapshot.source_hash | char(64), R | SHA-256 canonical input |
| DE-VN-PAY-004 | PayLine.category | enum, R | Earning/tax/insurance/deduction |
| DE-VN-PAY-005 | PayLine.amount_vnd | Decimal/Int, R | Cấu hình rounding |
| DE-VN-PAY-006 | PayLine.rule_version | varchar(64), R | Reproduce payslip |
| DE-VN-PAY-007 | PayRunAdjustment.original_payslip_id | FK, R | Không update phiếu Paid |
| DE-VN-PAY-008 | BankReconciliation.bank_reference | varchar nullable | Không lưu chứng từ có secrets trong log |
| DE-VN-SEC-001 | DataScopeGrant.company_id | FK, R | Không grant cross-tenant vô hạn |
| DE-VN-SEC-002 | SensitiveAccessLog.action/actor/time | enum/FK/datetime, R | Log không ghi raw CCCD, lương nếu tránh được |

## 4. Quan hệ dữ liệu và bất biến
- `Employee 1—N EmploymentAssignment`; `Employee 1—N Contract`; `Contract 1—N ContractAmendment`; `Employee 1—N Dependent`; `Dependent 1—N Eligibility`.
- `Company 1—N WorkLocation`; `Employee 1—N AttendanceEvent`; `AttendanceDecision N—1 WorkDate`; `LeaveRequest 1—N LeaveLedgerEvent`.
- `PayrollBatch 1—N Payslip`; `Payslip 1—N PayLine`; `Payslip N—1 RuleSetVersion` hoặc link qua snapshot; `Adjustment N—1 OriginalPayslip`.
- Tất cả tài liệu đính kèm cần metadata loại, phiên bản, hash, phân loại dữ liệu, người tải và chính sách lưu trữ; không lưu công khai URL không kiểm soát.

## 5. Quy tắc migrate & kiểm soát dữ liệu
1. Kiểm kê bản ghi trùng/thiếu, báo cáo trước khi sửa; tạo backup DB+media và diễn tập restore.
2. Tạo migration bổ sung và backfill bằng script idempotent; đếm bản ghi trước/sau; chưa đủ dữ liệu thì để trạng thái cần bổ sung thay vì giá trị giả.
3. Tiền lương/HĐ đã có giữ snapshot và nguyên bản; không chạy tính toán tự động để viết lại quá khứ.
4. Thử nghiệm cách map `Employee.first_name/last_name` sang hiển thị họ tên tiếng Việt; giữ nguyên nguyên liệu trước khi normalize.
5. Mọi API/export phải chạy qua tenant scope; thử query bằng nhiều tài khoản để kiểm tra object leakage.
6. Mốc hiệu lực địa giới, mức lương vùng, quy tắc thuế/BH không được khai báo kiểu global chỉ có một giá trị hiện tại.

## 6. Việc cần xác nhận trước DDL
Đối tượng lao động Việt Nam/người nước ngoài; một hay nhiều HĐLĐ đồng thời; multi-company; tổ chức dữ liệu cá nhân và consent theo trường hợp; chính sách mã hóa và khóa; đồng nhất mã ngân hàng; nguồn master data địa giới; thời hạn lưu hồ sơ; kiến trúc đồng bộ upstream. Không mở migration production trước khi HR/Kế toán/Tech Lead ký duyệt.
