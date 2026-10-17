# HORILLA HRM — PHÂN TÍCH GAP & KẾ HOẠCH VIỆT NAM HÓA

> **BẢN TỔNG QUAN — CẬP NHẬT HỆ TÀI LIỆU NGHIỆP VỤ 17/10/2026**  
> Phạm vi chi tiết đã tách thành [STD-00](00-QUY-UOC-VA-THUAT-NGU.md), [BRD-01](01-BRD-CHUC-NANG-VA-QUY-TRINH.md), [SRS-02](02-SRS-USE-CASE-VA-BUSINESS-RULE.md), [DATA-03](03-TU-DIEN-DU-LIEU-VA-ANH-XA-CODE.md), [OPS-04](04-CHAM-CONG-CA-LAM-NGHI-PHEP.md), [PAY-05](05-TINH-LUONG-THUE-BAO-HIEM.md), [LEGAL-06](06-DANG-KY-PHAP-LY-VA-POLICY-DECISION-LOG.md), [SEC-07](07-BAO-MAT-PHAN-QUYEN-BAO-CAO.md), [DEL-08](08-UAT-TRACEABILITY-ROADMAP.md), [UI-09](09-CHUAN-HOA-GIAO-DIEN-VA-THONG-DIEP-VI.md). Xem [mục lục](README.md). Nếu có khác biệt về số liệu luật, áp dụng sổ LEGAL-06 và quy tắc đã được thẩm định, **không tự sử dụng bản tổng quan này để tính tiền lương thật**. Các phần code mới chỉ là TO-BE; chưa chạy runtime/UAT.


**Ngày lập:** 17/10/2026  
**Repository:** https://github.com/dovandatym1-ship-it/horilla-hr  
**Baseline:** nhánh `2.0`, commit `fad3c73f212bd9a591b743024a1e6870e01f0f20` (commit ngày 15/10/2026), `horilla/__version__.py` = `2.1.8`  
**Phạm vi:** Đánh giá tĩnh cấu trúc repository và mẫu mã nguồn đại diện của từng miền nghiệp vụ, đối chiếu yêu cầu HRM doanh nghiệp Việt Nam. **Chưa** chạy hệ thống, test suite, benchmark, pentest, kiểm thử tích hợp, hoặc xác nhận tất cả luồng UI.

## 1. Quyết định sản phẩm

**Giữ Horilla làm hệ thống nền, tạo lớp `vn_hrm`/`vn_compliance` mở rộng và kiểm soát các điểm tích hợp vào lõi. Không viết lại ứng dụng từ đầu, không dịch giao diện rồi tuyên bố hệ thống đã tuân thủ pháp luật Việt Nam.**

Phân biệt hai mức:

1. **Việt hóa kỹ thuật:** ngôn ngữ, nhãn nghiệp vụ, `vi`, `vi_VN`, VND, `Asia/Ho_Chi_Minh`, định dạng `dd/MM/yyyy`, locale xuất nhập dữ liệu, tài liệu hướng dẫn.
2. **Việt Nam hóa nghiệp vụ:** hồ sơ nhân sự/CCCD/BHXH/MST, quản lý HĐLĐ, công chuẩn/nghỉ phép/ngày lễ, phụ cấp/làm thêm, khấu trừ bảo hiểm và thuế, thanh toán & đối soát lương, biểu mẫu/đối chiếu pháp định, bảo vệ dữ liệu cá nhân.

**Phạm vi khuyến nghị:** doanh nghiệp Việt Nam 50–500 lao động, 1–5 pháp nhân/chi nhánh, nhân viên văn phòng và ca kíp cơ bản, trả lương tháng bằng VND. Trường hợp lao động nước ngoài, doanh nghiệp lớn, xây dựng theo công trình, sản xuất 3 ca, tập đoàn đa quốc gia được đưa vào mở rộng sau khi xác nhận phạm vi.

## 2. Căn cứ mã nguồn

| Thành phần | File/folder đã kiểm tra | Tình trạng và phát hiện |
|---|---|---|
| Runtime | `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `docker-compose.prod.yml` | Python 3.12–3.14 theo README/requirements, Django 5.2.x, PostgreSQL 16, Redis 7, Docker/nginx, scheduler riêng. |
| Cấu hình | `horilla/settings/base.py`, `horilla/settings/security.py` | Có i18n, JWT + tenant scope, bảo vệ môi trường production; mặc định `LANGUAGE_CODE=en-us`, `TIME_ZONE=Asia/Kolkata`; thiếu `vi` trong `LANGUAGES`. |
| Ngôn ngữ | `horilla/locale/`, `horilla/horilla_middlewares.py` | Có 12 thư mục ngôn ngữ khác, chưa có `vi`. Middleware ưu tiên ngôn ngữ mặc định trừ khi người dùng chủ động chọn. |
| Công ty/tổ chức | `base/models.py`, `base/horilla_company_manager.py` | Có `Company`, `Department`, `JobPosition`, `JobRole`, loại nhân viên, ca làm, lịch nghỉ. Địa chỉ công ty là `country/state/city/zip` dạng text. |
| Hồ sơ nhân sự | `employee/models.py` | `Employee`, `EmployeeWorkInformation`, `EmployeeBankDetails` có nền dữ liệu; chưa thấy trường chuyên biệt CCCD, số BHXH, MST cá nhân trong các model chính đã đọc. Có `additional_info` JSON. |
| Tuyển dụng | `recruitment/models.py` | `Recruitment`, `Stage`, `Candidate`, lịch phỏng vấn, hồ sơ, document. Tận dụng phần lớn. |
| On/offboarding | `onboarding/models.py`, `offboarding/models.py` | Có stage/task/portal; có thư nghỉ việc và lý do; cần mẫu bàn giao Việt Nam. |
| Chấm công | `attendance/models.py`, `attendance/views/`, `biometric/`, `geofencing/` | Có check-in/out, giờ làm, overtime, xác nhận, xử lý xung đột, nguồn thiết bị/địa lý. Cần chốt quy tắc công chuẩn và ca đêm/qua ngày. |
| Nghỉ phép | `leave/models.py` | `LeaveType`, `AvailableLeave`, `LeaveRequest`, ngày phép chuyển kỳ, nghỉ bù, phê duyệt; cần policy theo luật và theo thâm niên. |
| Hợp đồng | `payroll/models/models.py` | `Contract` có hiệu lực, kỳ trả, wage, loại thù lao; cần bổ sung loại HĐLĐ pháp định, thử việc, lịch sử phụ lục, ngày ký, hiệu lực, cảnh báo. |
| Lương | `payroll/methods/payroll_run.py`, `payslip_calc.py`, `component_engine.py`, `payroll/models/payroll_batch.py` | Tính thành phần lương và deductions; tách OT thường/ngày nghỉ/ngày lễ; có lô lương trạng thái draft/review/approved/paid, paid không được quay lại. |
| Thuế & bảo hiểm | `payroll/tax_packs.py`, `payroll/methods/tax_calc.py`, `contributions.py`, `payroll/models/tax_models.py` | Có cấu hình thuế theo bracket và đóng góp của doanh nghiệp, nhưng **không có bộ mặc định Việt Nam** trong `tax_packs.py`; engine dùng nhiều `FloatField` và `float`. |
| PMS | `pms/models.py` | Có kỳ đánh giá, objectives/KR/feedback. Chủ yếu dịch và cấu hình. |
| Project/Timesheet | `project/models.py` | Có `Project`, `Task`, `TimeSheet`; có thể dùng sau MVP. |
| Báo cáo | `report/models.py`, `report/registry.py` | Có registry, saved views, subscriptions, xuất báo cáo; bổ sung bộ báo cáo nội địa, chuẩn hóa quyền và định dạng. |
| Bảo mật | `horilla_api/authentication.py`, `horilla_auth`, `horilla_audit`, `base/tests` | Có JWT xác thực theo công ty, audit và test boundary; cần kiểm thử thâm nhập, phân quyền trường dữ liệu và xuất file. |
| Tích hợp/API | `horilla_api/api_urls/`, `horilla_api/api_views/`, `horilla_api/README_API_DOCS.md` | Đã phân chia API theo module; có Swagger/ReDoc và JWT. |
| Khác | `asset`, `helpdesk`, `horilla_documents`, `horilla_ldap`, `horilla_automations`, `horilla_backup`, `horilla_theme` | Giữ làm module hỗ trợ hoặc triển khai có chọn lọc. |
| Kiểm thử/CI | `.github/workflows/`, `payroll/tests/`, `attendance/tests/`, `leave/tests/`, `report/tests/` | Có `unit-tests.yml`, `quality.yml`, `codeql.yml`, `docker-ci.yml` và payroll golden fixture. Chưa chạy, chưa xác nhận pass trên fork. |

**Điểm đáng chú ý:** README nhắc Docker tag `2.1.5`, còn `horilla/__version__.py` ở baseline ghi `2.1.8`: khi đóng gói phải pin **commit + image digest** của bản đã test, không phụ thuộc tag được minh họa trong README.

## 3. Ma trận GAP & quyết định dùng/sửa/xây

| Mã | Nhóm | Có sẵn trong lõi | GAP cho Việt Nam | Hướng làm | Ưu tiên |
|---|---|---|---|---|---|
| VN-PLT-01 | Locale | Django i18n, locale khác | Thiếu `vi`, chuẩn thuật ngữ, lỗi nội dung hardcode chưa kiểm kê | Bổ sung `vi`, dịch và kiểm tra UI/API/export | P0 |
| VN-PLT-02 | Cấu hình VN | Setting ngôn ngữ/múi giờ/định dạng | Default Ấn Độ/Anh, currency `$` | Cấu hình theo pháp nhân, VND, Asia/Ho_Chi_Minh, lịch, số | P0 |
| VN-ORG-01 | Công ty/chi nhánh | Company, Department, Role | MST tổ chức, địa chỉ Việt Nam, vùng lương, mã đơn vị BHXH | `VnCompanyProfile`, đơn vị hành chính theo hiệu lực | P0 |
| VN-EMP-01 | Hồ sơ nhân viên | Employee, WorkInfo, Bank | CCCD, ngày cấp, cơ quan cấp, MST, BHXH, tư cách cư trú, người phụ thuộc | Model pháp lý riêng và phân quyền ở mức trường | P0 |
| VN-CON-01 | HĐLĐ | Contract và trạng thái | Loại HĐLĐ, thử việc, phụ lục, ngày ký, lịch sử điều chỉnh, cảnh báo hạn | `VnContractDetail`, `VnContractAmendment` | P0 |
| VN-ATT-01 | Công/ca | Shift, Attendance, overtime | Công chuẩn; đi muộn/về sớm; ca đêm/qua ngày; nghỉ lễ; loại giờ OT theo điều kiện VN | Policy + giờ gốc có log + đối soát | P0 |
| VN-LEV-01 | Nghỉ phép | Loại nghỉ, balance, carryforward | Phép theo thâm niên, đối tượng, nghỉ việc; nghỉ hưởng chế độ bảo hiểm | Rule theo effective date, ledger và test | P0 |
| VN-PAY-01 | Bảng lương | Contract, batch, payslip, components | Chưa có bộ điều kiện VN, chốt kỳ/điều chỉnh/gross-net chuẩn | Adapter tính VND + snapshots + duyệt và khóa kỳ | P0 |
| VN-INS-01 | BHXH/BHYT/BHTN | Generic contribution deductions | Đối tượng, nền tính đóng, trần/sàn, tăng giảm, truy thu, nghỉ không lương | `VnInsurancePolicy`, Enrollment, monthly statement | P0 |
| VN-TAX-01 | Thuế TNCN | FilingStatus, TaxBracket, tax engine | Thuế cư trú/không cư trú, phụ thuộc, miễn trừ, quyết toán, quy tắc theo năm | `VnPitPolicy`, `VnTaxDependent`, calculator độc lập | P0 |
| VN-REP-01 | Mẫu biểu | Report engine, PDF/Excel | Bảng công/lương VN, báo cáo thuế/bảo hiểm, xuất ngân hàng | Template versioned, xuất Excel/PDF kiểm soát quyền | P0/P1 |
| VN-SEC-01 | Dữ liệu cá nhân | Auth, JWT, audit, export checks | Dữ liệu định danh/thuế/lương nhạy cảm, yêu cầu truy cập/xóa/lưu trữ | Phân loại dữ liệu, consent/notice, RBAC/field ACL, log | P0 |
| VN-REC-01 | Tuyển dụng | ATS giàu tính năng | Form/mẫu offer và thư VN | Localization, mẫu biểu | P1 |
| VN-ONB-01 | Tiếp nhận/bàn giao | On/offboarding task | Checklist thử việc, cấp tài khoản/tài sản, hồ sơ BH, chấm dứt HĐ | Mẫu quy trình | P1 |
| VN-PMS-01 | Đánh giá | OKR/KR/Feedback | Thang đánh giá/mẫu phiếu VN | Cấu hình | P2 |
| VN-OPS-01 | Asset/Helpdesk/Project | Có module độc lập | Chưa cần cho core HR | Bật theo nhu cầu sau MVP | P2 |
| VN-INT-01 | Tích hợp | REST + biometric + LDAP | Đầu đọc chấm công nội địa, ngân hàng, hóa đơn/kế toán | API adapter/import/export, không cam kết có API đối tác | P1/P2 |

**P0:** cần trước khi đưa nhân sự/chấm công/lương thực vào vận hành. **P1:** tăng mức hữu dụng. **P2:** mở rộng, không cản trở MVP.

## 4. Thiết kế dữ liệu dự kiến

Không ghi số CCCD/MST/BHXH trực tiếp vào `additional_info` JSON nếu dữ liệu phải có validation, tìm kiếm, phân quyền và audit riêng. Tạo các bảng có khóa ngoại tới `employee.Employee`, `base.Company`, `payroll.Contract`:

- **`VnCompanyProfile`**: company, tax_code, insurance_unit_code, registered_address, current_province_code, current_ward_code, minimum_wage_region, valid_from/valid_to.
- **`VnAdministrativeUnit`**: code, name, level (province/commune), parent_code, valid_from/to, source_version, legacy_mapping. **Không bắt buộc cấp huyện trong schema địa chỉ hiện hành**; lưu mã cũ cho dữ liệu lịch sử nếu có.
- **`VnEmployeeLegalProfile`**: employee, citizenship/residency, identity_type, identity_number (encrypted/tokenized), issue_date/place, tax_id, social_insurance_no, personal_tax_status, effective dates; audit and masking.
- **`VnDependent`**: employee, relationship, identity/tax id, registration_date, eligible_from/to, verification_status; không mặc định số con = số người phụ thuộc thuế.
- **`VnContractDetail`**: contract, lawful_contract_type, probation_start/end, sign_date, workplace, statutory/insurance_salary bases, salary_form, union data if needed, notification deadlines.
- **`VnContractAmendment`**: contract, version, effective_date, approved_by, salary/policy change, document reference; lịch sử bất biến.
- **`VnWorkPolicy`**: company/location, standard_hours, wage_days_basis, night_window, overtime_approval, rounding_policy, valid_from/to.
- **`VnLeavePolicy`**: leave_type, employee_group, accrual/eligibility/carryover, seniority_rule, service_effective_dates.
- **`VnInsuranceEnrollment`**: employee, company, scheme, employee/employer applicability, contribution_base, rate plan, start/end, temporary suspension, adjustment reason.
- **`VnComplianceRuleVersion`**: domain (TAX/INSURANCE/MIN_WAGE/OVERTIME), legal_reference, effective_from/to, rates/parameters JSON (validated), approved_by, change_reason, immutable after activation.
- **`VnPayrollRunSnapshot`**: batch_id, employee_id, contract_version, attendance_hash, approved_leave_hash, policy_version, input_hash, earnings, deductions, employer_cost, net_pay, computed_at, approved_at; VND integer units hoặc Decimal được lượng tử hóa.
- **`VnPayrollAdjustment`**: target period, origin period, employee, signed_amount, reason, linked approved run — điều chỉnh kỳ mới thay vì sửa kỳ đã trả.
- **`VnBankPaymentExport`**: batch, bank, exported_by, export_hash, exported_at, disbursement_state; lưu trạng thái, không tự nhận giao dịch ngân hàng thành công.
- **`VnSensitiveDataAccessLog`**: actor, subject, field group, action, timestamp, purpose, request_id; không ghi nguyên giá trị bí mật vào log.

Quy tắc DB: migration không phá schema gốc, `UniqueConstraint` phù hợp, index theo employee/company/effective period, thông tin nhạy cảm cần mã hóa và tra cứu qua mã băm kiểm soát; không `CASCADE` làm mất hồ sơ pháp lý đã chốt khi xóa tài khoản. Kiểm tra các quan hệ tồn tại trước khi thiết kế hành vi xóa.

## 5. Thiết kế luồng nghiệp vụ

### 5.1. Nhân viên mới

Tạo hồ sơ tuyển dụng → chuyển nhân viên → nhập hồ sơ pháp lý → hợp đồng/thử việc → gán công ty/bộ phận/ca → thiết lập tham gia bảo hiểm và thuế → cấp tài khoản và phân quyền → lưu checklist tiếp nhận. Cần tách ngày vào làm, ngày bắt đầu HĐLĐ, ngày bắt đầu đóng bảo hiểm và ngày tính thu nhập chịu thuế; **không dùng một ngày đại diện cho mọi nghiệp vụ**.

### 5.2. Công và nghỉ

Nguồn check-in/out → lưu sự kiện thô & nguồn → ghép ca làm/qua ngày → phát hiện thiếu chấm công → nhân viên yêu cầu giải trình → người quản lý phê duyệt → tính ngày công & OT theo công ty, địa điểm, loại ngày → khóa kỳ công → cấp snapshot cho Payroll. Phép theo năm/thâm niên được tính trên ledger; thay đổi phép sau khi đã chốt lương phải tạo điều chỉnh.

### 5.3. Lương

Chọn kỳ lương/pháp nhân → xác nhận chính sách hợp lệ theo thời điểm → kiểm tra hợp đồng, công, nghỉ, người phụ thuộc, bảo hiểm → tính gross thu nhập → các khoản giảm trừ chịu thuế/không chịu thuế đúng danh mục → BHXH/BHYT/BHTN của NLĐ → PIT theo tư cách cư trú, kỳ áp dụng, loại hợp đồng → các khoản khấu trừ hợp lệ khác → net pay → chi phí doanh nghiệp → đối chiếu tiền và công → duyệt 2 cấp → xuất lệnh ngân hàng → đánh dấu đã trả sau xác nhận → khóa kỳ. Sai sót sau trả: **adjustment ở kỳ sau, không ghi đè snapshot kỳ cũ.**

Đặc biệt: logic `payroll/methods/payslip_calc.py` đã chia OT thành regular/week off/holiday; nhưng tỷ lệ tiền cụ thể và các trường hợp ngày lễ trùng ngày nghỉ, làm đêm và OT ban đêm phải dựa vào **VN rule engine**. Không mặc định chỉ thay 150/200/300% là đủ.

### 5.4. Nghỉ việc

Đề nghị nghỉ → điều kiện báo trước & phê duyệt theo trường hợp → bàn giao & thu hồi quyền → chốt công/phép/lương thưởng & nghĩa vụ → xử lý tham gia BHXH → lập hồ sơ chấm dứt → đóng tài khoản và lưu chứng từ theo thời hạn áp dụng.

## 6. Cơ sở pháp lý để đóng băng business rules (tại 17/10/2026)

| Nhóm | Văn bản trọng tâm | Ảnh hưởng chức năng |
|---|---|---|
| Lao động | Bộ luật Lao động 45/2019/QH14 và Nghị định 145/2020/NĐ-CP; kiểm tra sửa đổi/hướng dẫn còn áp dụng | HĐLĐ, thời giờ, nghỉ lễ/nghỉ phép, làm thêm, nghỉ việc |
| BHXH | Luật BHXH 41/2024/QH15 (hiệu lực từ 01/07/2025), cùng văn bản sửa đổi/hợp nhất và hướng dẫn tới thời điểm triển khai | Đối tượng tham gia, mức căn cứ, tăng giảm, chế độ |
| BHYT | Luật 51/2024/QH15 sửa đổi Luật BHYT, hiệu lực 01/07/2025 | Đối tượng và mức đóng BHYT |
| BHTN | Luật Việc làm 74/2025/QH15, hiệu lực 01/01/2026, cùng văn bản hướng dẫn | Đối tượng, đóng, nghĩa vụ |
| Thuế TNCN | Luật 109/2025/QH15 hiệu lực 01/07/2026; quy định tiền lương/tiền công cá nhân cư trú áp dụng từ kỳ tính thuế 2026; Nghị định 253/2026/NĐ-CP | Biểu thuế 5 bậc, giảm trừ, thu nhập miễn/không miễn, hồ sơ quyết toán |
| Giảm trừ gia cảnh | Nghị quyết 110/2025/UBTVQH15 và Luật 109/2025/QH15 | 15,5 triệu VND/tháng cho bản thân; 6,2 triệu VND/tháng/người phụ thuộc cho kỳ tính thuế 2026 |
| Lương tối thiểu | Nghị định 293/2025/NĐ-CP, hiệu lực 01/01/2026 | Vùng I 5.310.000; II 4.730.000; III 4.140.000; IV 3.700.000 VND/tháng; vùng theo nơi hoạt động |
| Dữ liệu cá nhân | Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15 hiệu lực 01/01/2026 và hướng dẫn | Phân loại, thông báo, quyền chủ thể, thời hạn, biện pháp bảo mật, đánh giá/biên bản theo nghĩa vụ thực tế |
| Địa giới hành chính | Quy định địa giới hiện hành, mô hình chính quyền 2 cấp từ 2025 | Chuẩn hóa mã tỉnh/thành và xã/phường/đặc khu, giữ lịch sử địa chỉ cũ |

**Lưu ý pháp chế:** Một số cổng tra cứu hiển thị trạng thái hiệu lực khác nhau cho Luật BHXH 41/2024. Trước khi công bố bộ rule sản xuất, cần đối chiếu **văn bản hợp nhất và văn bản sửa đổi mới nhất**, do nhân sự pháp chế/kế toán phụ trách ký duyệt. Không hardcode mức trần, tỷ lệ, biểu mẫu nếu chưa xác minh văn bản thực thi tại ngày có hiệu lực.

Nguồn tham khảo nhà nước:  
- https://vanban.chinhphu.vn/?classid=1&docid=198540&pageid=27160  
- https://vanban.chinhphu.vn/default.aspx?docid=201967&pageid=27160  
- https://vanban.chinhphu.vn/?classid=1&docid=211199&pageid=27160  
- https://vanban.chinhphu.vn/?classid=1&docid=214560&pageid=27160  
- https://vanban.chinhphu.vn/?docid=216495&pageid=27160  
- https://xaydungchinhsach.chinhphu.vn/quy-dinh-giam-tru-gia-canh-119260703144038062.htm  
- https://xaydungchinhsach.chinhphu.vn/nghi-dinh-so-293-2025-nd-cp-quy-dinh-muc-luong-toi-thieu-doi-voi-nguoi-lao-dong-lam-viec-theo-hop-dong-lao-dong-119251110172808433.htm  
- https://vanban.chinhphu.vn/?docid=214590&pageid=27160

## 7. Đề xuất tổ chức code

```text
horilla-hr/
├── horilla/                     # Core: sửa tối thiểu để add app và locale
│   ├── locale/vi/LC_MESSAGES/  # Django gettext messages
│   └── settings/base.py         # settings i18n, timezone, INSTALLED_APPS
├── vn_hrm/                      # Django app mới: master data, employee legal, contract
│   ├── models.py
│   ├── forms.py
│   ├── services/
│   ├── permissions.py
│   ├── views/
│   ├── api/
│   ├── templates/
│   ├── migrations/
│   └── tests/
├── vn_payroll/                  # Django app mới: policies/rules/adapter/snapshots
│   ├── models.py
│   ├── policy_registry.py
│   ├── calculators/{tax,insurance,overtime,net_pay}.py
│   ├── services/{payroll_bridge,close_period,adjustment}.py
│   ├── exports/
│   └── tests/{fixtures,golden,regression}/
├── vn_reports/                  # Local reports, payslip, bank templates
│   ├── registry.py
│   ├── templates/
│   └── tests/
└── docs/vietnam/                # BRD, SRS, glossary, legal decision log
```

**Tối thiểu thay lõi**:
- `horilla/settings/base.py`: đăng ký app, `vi`, timezone env & locale; chỉ chỉnh sau baseline test.
- `horilla/locale/vi/...`: thông điệp.
- `payroll/methods/payroll_run.py`/`batch_run.py`: chỉ thêm **một điểm adapter có test** nếu hệ thống chưa có integration hook đủ an toàn; tuyệt đối không phân nhánh logic VN nằm rải ở hàng chục file.
- `employee/`, `base/`, `leave/`, `attendance/`: chỉ chỉnh UI/validation hoặc hook không thể mở rộng bằng app riêng.
- API phải giữ cùng tenant scope bằng `TenantScopedJWTAuthentication`; không triển khai endpoint riêng bỏ qua RBAC/tenant permission.

**Lưu ý thiết kế:** đây là cây thư mục **đề xuất xây mới**, không phải mô tả các file đã tồn tại.

## 8. Danh sách Epic / Feature sẵn sàng đưa vào backlog

| Epic | Feature | Công việc trọng tâm | Nghiệm thu |
|---|---|---|---|
| E-VN-01 | F-VN-001 | Baseline, chạy được dev/test/prod mẫu | Docker, migrations, smoke + core tests có kết quả ghi nhận |
| E-VN-01 | F-VN-002 | i18n toàn hệ thống | Trang menu/form/button/error/notification dịch; fallback EN không lỗi |
| E-VN-01 | F-VN-003 | VND, ngày tháng, múi giờ | Nhất quán Web/API/Excel/PDF; không làm sai timestamps UTC |
| E-VN-02 | F-VN-004 | Hồ sơ pháp nhân, địa chỉ VN | Mã tỉnh/xã, vùng lương theo địa điểm/effective date |
| E-VN-02 | F-VN-005 | Hồ sơ định danh nhân viên | CCCD/MST/BHXH có kiểm tra, che dữ liệu, RBAC, audit |
| E-VN-02 | F-VN-006 | Người phụ thuộc thuế | Có hồ sơ và thời gian áp dụng, không suy từ số con |
| E-VN-03 | F-VN-007 | Quản lý hợp đồng VN | HĐ có thời hạn/không thời hạn, thử việc, phụ lục, cảnh báo |
| E-VN-04 | F-VN-008 | Chốt công Việt Nam | Công chuẩn/ca đêm/qua ngày, xung đột xử lý trước payroll |
| E-VN-04 | F-VN-009 | OT theo loại ngày & ca đêm | Tách tiền OT chuẩn rule, không trả trùng số giờ |
| E-VN-04 | F-VN-010 | Phép/lễ/nghỉ chế độ | Số dư và ngày nghỉ đúng cấu hình hợp lệ, cân đối ledger |
| E-VN-05 | F-VN-011 | Cấu hình luật theo hiệu lực | Rule có version, legal ref, approval, rollover |
| E-VN-05 | F-VN-012 | Thu nhập/khấu trừ gross-net | VND deterministic, trace từng khoản và căn cứ |
| E-VN-05 | F-VN-013 | Bảo hiểm bắt buộc | Phân biệt NLĐ/doanh nghiệp, mức đóng, thời hạn, đối soát |
| E-VN-05 | F-VN-014 | TNCN và giảm trừ | Người phụ thuộc, tình trạng cư trú, biểu 2026, test golden |
| E-VN-05 | F-VN-015 | Chốt duyệt kỳ lương | Draft→Review→Approved→Paid, snapshot không ghi đè |
| E-VN-06 | F-VN-016 | Báo cáo công/lương và sao kê | Excel/PDF đúng font Việt, template, quyền truy cập |
| E-VN-06 | F-VN-017 | Export ngân hàng | File không sai dấu/tiền, hash, reconciliation |
| E-VN-07 | F-VN-018 | Kiểm soát dữ liệu cá nhân | Phân quyền lĩnh vực và cột, log export/view, retention |
| E-VN-07 | F-VN-019 | Security + integration regression | Không rò rỉ giữa pháp nhân, endpoint bảo mật và role |
| E-VN-08 | F-VN-020 | UAT + vận hành & đào tạo | Biên bản kiểm thử ký duyệt, SOP, rollback/drills |

### Phân rã ví dụ F-VN-014 (thuế TNCN)

**Actors:** HR Payroll, Kế toán tiền lương, Trưởng bộ phận chỉ đọc thông tin được phân quyền, NLĐ xem phiếu lương của mình.  
**Inputs:** hợp đồng, công/nghỉ, thành phần thu nhập, đối tượng cư trú, hồ sơ người phụ thuộc theo thời gian, các khoản miễn/giảm theo luật, kỳ lương, policy version.  
**Preconditions:** bảng công đã chốt; HĐ có hiệu lực; tất cả dòng thu nhập có phân loại thuế; policy được duyệt.  
**Main flow:** xác định khoản chịu thuế → xác định khoản giảm trừ và phụ thuộc theo kỳ → áp biểu phù hợp → làm tròn chính sách VND → lưu diễn giải từng bước và phiên bản tính toán → soát chênh với kỳ trước.  
**Exceptions:** nhân viên vào/ra giữa kỳ; nhập mới người phụ thuộc có hiệu lực hồi tố; hai khoản lương nhiều lần một tháng; cư trú thay đổi; không đủ dữ liệu; truy thu/hoàn thuế.  
**Postconditions:** có số thuế và audit, không sửa phiếu lương đã paid; chênh lệch có adjustment riêng.

## 9. Roadmap triển khai đề xuất

**Giả định nhân sự:** 1 BA/PM, 2 backend Django, 1 frontend/UI (có thể kiêm Python template), 1 QA; kế toán/HR và pháp chế tham gia UAT và duyệt policy. Đây là ước lượng triển khai, **không phải số đo thực tế của repository**.

| Phase | Thời gian ước tính | Phạm vi | Deliverables và gate |
|---|---|---|---|
| P0 — Audit & baseline | Tuần 1–2 | Clone, migration, cấu hình, smoke, CI, security baseline; khóa scope pháp nhân/quy mô | `architecture.md`, GAP, baseline-test report, BRD v1 |
| P1 — Foundation VN | Tuần 3–4 | i18n, VND, timezone, danh mục địa giới, policy registry skeleton | `vi`, localization tests, data dictionary |
| P2 — Hồ sơ/HĐ | Tuần 5–7 | Legal profile, dependents, công ty/chi nhánh, hợp đồng và phụ lục | Employee/Contract SRS, migration, test quyền |
| P3 — Công/phép | Tuần 8–10 | Công chuẩn, ca, OT, ngày lễ, phép và khóa dữ liệu kỳ | Attendance/Leave goldens, UAT nghiệp vụ |
| P4 — Payroll VN | Tuần 11–16 | Thành phần VND, BH, PIT, snapshot, approvals, adjustment | Payroll goldens, đối chiếu Excel, 2 kỳ chạy song song |
| P5 — Báo cáo/tích hợp | Tuần 17–18 | Phiếu lương VN, Excel/PDF, export ngân hàng, dữ liệu pháp định mức MVP | Report templates, export security tests |
| P6 — Hardening & Go-live | Tuần 19–20 | Security review, performance, backup/restore, đào tạo, diễn tập rollback | UAT sign-off, readiness checklist, SOP |

Các phase có thể chồng lắp 2–4 tuần, nhưng **không đưa payroll thật vào chạy** trước khi HR & kế toán đối chiếu thành công 2 kỳ và ký duyệt rule. Nếu chỉ cần **MVP quản lý HR + chấm công + nghỉ phép chưa trả lương pháp định**, có thể mục tiêu 8–12 tuần. Hệ thống đủ các tích hợp/nhiều doanh nghiệp và chuẩn tuân thủ mở rộng có thể 6–9 tháng.

## 10. Ma trận vai trò và quyền tối thiểu

| Vai trò | Employee | Contract | Attendance | Payroll | Export dữ liệu nhạy cảm |
|---|---|---|---|---|---|
| HR Admin | CRUD có phạm vi công ty | CRUD theo phân quyền | Xem/chỉnh theo approval | Chỉ dữ liệu được cho phép | Chỉ được cấp riêng |
| Payroll Specialist | Xem hồ sơ tối thiểu | Xem phần lương | Xem kỳ đã chốt | Tạo và soát kỳ; không tự duyệt | Có log và kiểm duyệt |
| Finance Approver | Xem thông tin thanh toán tối thiểu | Xem tài chính theo quyền | Xem tổng hợp | Duyệt, không tự tạo/chỉnh dòng gốc | Xuất ngân hàng theo vai trò |
| Line Manager | Xem nhân sự dưới quyền | Không mặc định thấy lương | Xem & duyệt yêu cầu đội nhóm | Không thấy lương nếu không cấp rõ | Không |
| Employee (ESS) | Chỉ bản thân | Xem HĐ mình | Gửi yêu cầu/sửa có duyệt | Chỉ phiếu lương của mình | Chỉ của bản thân |
| System Admin | Quản lý cấu hình | Không mặc nhiên đọc CCCD/lương | Cấu hình | Không tự động có quyền chi trả | Theo kiểm soát đặc biệt |

Cần thử tổ hợp vai trò + pháp nhân + API + xuất dữ liệu, không chỉ ẩn nút trên giao diện.

## 11. Bộ kiểm thử bắt buộc và chỉ tiêu UAT

### Functional golden cases tối thiểu

1. Nhân viên mới giữa tháng, công chuẩn tính đúng và không nhân đôi lương.
2. Hợp đồng không thời hạn và xác định thời hạn; thử việc; phụ lục tăng lương giữa kỳ.
3. Ca qua đêm 22:00–06:00, đi muộn, nghỉ giữa ca, clock-out hôm sau.
4. OT ngày thường/ngày nghỉ/ngày lễ; làm đêm và OT ban đêm; không double-count.
5. Nghỉ phép cả ngày/nửa ngày, nghỉ không lương, nghỉ bù, phép chuyển năm, thâm niên.
6. Mức lương tối thiểu vùng theo nơi làm việc + mốc hiệu lực thay đổi.
7. Tách khoản lương tính thuế, miễn thuế; tình trạng cư trú và khoản khấu trừ theo hợp đồng.
8. Người phụ thuộc phát sinh/giảm giữa năm, ngày hiệu lực khác ngày nhập liệu.
9. Bảo hiểm cho nhân viên, doanh nghiệp; nghỉ không lương, thay đổi căn cứ và giới hạn đóng.
10. Lương thay đổi sau khi chốt công; quy trình điều chỉnh kỳ kế tiếp.
11. Employee A thuộc Company A không xem/export dữ liệu Company B qua direct API ID.
12. Chỉ người có quyền được đọc/tải hợp đồng, CCCD, số tài khoản, bảng lương.
13. Xuất Excel/CSV UTF-8, tên tiếng Việt có dấu, zero-leading account numbers.
14. Export và import lặp lại không tạo duplicate hoặc chi trả lặp.
15. Batch đã paid không thể quay về draft/ghi đè tiền; mọi điều chỉnh có trace.
16. Backup/restore giữ được file hồ sơ, dữ liệu payroll, audit, job scheduling.

### Gate định lượng đề xuất

- **100%** phép tính trong bộ case mẫu được HR/Kế toán xác nhận đúng theo quy tắc đã duyệt; không tolerance lệch 1 đồng khi dùng VND integer rounding policy.
- **100%** case P0 & critical security pass; không còn blocker/high chưa có biện pháp chấp nhận rủi ro.
- **02 kỳ lương** chạy song song bằng cả hệ thống hiện hành và Horilla-VN, chênh lệch được giải thích bằng phiếu đối soát riêng.
- **0** truy cập chéo dữ liệu nhân sự/lương giữa doanh nghiệp hoặc ngoài phạm vi quyền.
- Có chỉ tiêu performance riêng theo quy mô (ví dụ 500 nhân sự, import file công 20.000 sự kiện), quyết định sau baseline benchmark.
- Khôi phục backup và rollback phải diễn tập, không chỉ có tài liệu.

## 12. Rủi ro và đối sách

| Rủi ro | Tác động | Biện pháp |
|---|---|---|
| Sửa lõi Horilla phân tán | Xung đột upstream khó nâng cấp | App extension, adapter tối thiểu, upstream diff review mỗi release |
| Quy định thuế/bảo hiểm đổi theo thời điểm | Tính sai tiền thực tế | Effective-dated version, pháp chế duyệt, snapshot và regression |
| `FloatField` và `float` trong tiền | Sai lệch làm tròn, đối soát VND | Decimal/integer VND ở adapter/output, tiêu chuẩn round, golden tests, không thay đại trà field gốc khi chưa migration plan |
| Scheduler không idempotent khi scale | Phát sinh job/lương lặp | Chạy một replica theo compose hiện có; nâng cấp job key/idempotency trước horizontal scaling |
| Rò rỉ dữ liệu CCCD/lương | Rủi ro pháp lý & uy tín | Field-level masking, export authorization, encryption, audit, secret rotation, retention |
| Cơ sở dữ liệu cũ thiếu trường | Đứt vòng đời nhân sự | Data dictionary, mapping, import staged, null/duplicate checks, backfill |
| Giữ nguyên mẫu quốc tế | Biểu mẫu VN không dùng được | BA validate theo doanh nghiệp thật, template version và preview |
| Thử vận hành chưa đủ | Sai lương, khó rollback | Parallel payroll 2 kỳ, UAT ký, backup/restore rehearsal |
| License LGPL-2.1 | Nghĩa vụ phân phối & thông báo | Review nghĩa vụ tương ứng mô hình phân phối, giữ notices, không xóa giấy phép, tư vấn pháp lý khi thương mại hóa |

## 13. Những việc **không** làm trong MVP

- Không viết lại frontend sang React/Vue khi chưa có tiêu chí lợi ích và benchmark.
- Không xây module kế toán tổng hợp/ERP mới.
- Không kết nối trực tiếp BHXH, cơ quan thuế, ngân hàng khi chưa có API/điều kiện pháp lý chính thức; chỉ hỗ trợ hồ sơ/xuất file có kiểm soát.
- Không xây AI chấm điểm nhân viên hoặc quyết định lương tự động không minh bạch.
- Không ép toàn bộ chính sách cứng theo một doanh nghiệp: mỗi company có policy riêng, nhưng luật nền tảng áp dụng theo thời gian và vùng.
- Không thiết kế cơ cấu địa giới bắt buộc cấp huyện cho địa chỉ mới của VN.

## 14. Việc cần chốt trước khi code (Decision Log)

1. Pháp nhân/chi nhánh bao nhiêu? 1 DN hay đa công ty? Có dùng nhiều khung lương/vùng không?
2. Quy mô nhân sự, ca đêm, nhân viên thời vụ/cộng tác/ngoài quốc tịch VN?
3. Công chuẩn 22/24/26 ngày hay lịch động, xử lý nghỉ thứ Bảy, chính sách thưởng chuyên cần?
4. Gross/Net/CTC, trả lương 1 hay 2 đợt, thời điểm khóa công, HĐ thử việc?
5. Bộ khoản phụ cấp, tính thuế/bảo hiểm riêng theo chính sách đúng pháp luật, khấu trừ nội bộ?
6. Đối tượng đóng BHXH/BHYT/BHTN theo doanh nghiệp/loại hợp đồng và quy định ngày áp dụng?
7. Công cụ trả lương và chuẩn file ngân hàng hiện tại; kế toán cần import sang gì?
8. Mức phân quyền xem CCCD/lương, dữ liệu lưu ở đâu, chính sách giữ/xóa dữ liệu?
9. Cần mobile ESS/chấm công QR/geofence/biometric đến mức nào?
10. Bộ chứng từ/mẫu báo cáo đang dùng, ai là người ký duyệt UAT và quy tắc pháp lý?

### Triển khai mã nguồn ở các PR tiếp theo

Nhánh `feature/vietnam-hrm-foundation` là bước đầu để đưa tài liệu vào repository. Các bản BRD/SRS/Data Dictionary/Business Rules/UAT mức tài liệu đã được tách trong `docs/vietnam/` (xem `README.md`). Sau khi duyệt, mới bổ sung skeleton các app, bản dịch `vi` và các bước tích hợp code trong những PR kỹ thuật riêng. PR hiện tại chỉ chứa tài liệu, chưa thay đổi tính năng HRM.

---

**Độ tin cậy:** kiểm tra trực tiếp mã nguồn tĩnh cho module/engine/nội dung được dẫn đường; đề xuất GAP khi thiếu cấu trúc trong các model và tệp liên quan đã đọc. Cụm “chưa có” không hàm ý đã exhaustively grep được mọi dòng/mọi nhánh. Phải tiếp tục chạy & kiểm tra chức năng thực tế ở P0. Bộ quy tắc pháp lý là yêu cầu phân tích, không thay cho ý kiến phê duyệt của chuyên gia lao động/thuế/bảo hiểm trước production.