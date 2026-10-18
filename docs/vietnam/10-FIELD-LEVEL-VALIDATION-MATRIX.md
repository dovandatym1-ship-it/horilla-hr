# VN-HRM | Ma trận validation từng trường dữ liệu
**ID:** VNHRM-VAL-10 · **Phiên bản:** 1.1 · **Ngày rà soát:** 18/10/2026 · **Trạng thái:** DRAFT/TO-BE, kiểm tra code tĩnh, chưa sign-off HR/Payroll/Pháp chế.

## 1. Cách đọc và phạm vi kiểm chứng
- **CODE**: kiểm tra thấy trong nhánh \`feature/vn-dynamic-hrm\` (PR #3); không đồng nghĩa runtime PASS. **SPEC**: yêu cầu cần bổ sung/triển khai, chưa xác nhận có trong code. **POLICY**: phụ thuộc quy chế/căn cứ có hiệu lực và quyết định được ký duyệt, không được hardcode. **GAP**: tài liệu/code không khớp.
- Cột **R** là bắt buộc nghiệp vụ; không tự động đồng nghĩa \`null=False\` trong migration. **U(scope)** là duy nhất trong phạm vi nêu rõ. Không ép kiểm tra định dạng giấy tờ ở các loại quốc tịch/giấy tờ chưa được xác nhận.
- **Validation contract**: xác thực phía server trong mọi API, form, import, bulk, admin và job; UI chỉ hỗ trợ phản hồi; không tin cậy thuộc tính disabled/hidden ở client. Phân biệt lỗi kiểu dữ liệu, độ dài, trùng, tham chiếu, trạng thái, quyền, thời gian hiệu lực và xung đột giao dịch.
- Mọi dòng SPEC/POLICY phải gắn UC, BR, TC; nếu chưa xác định quy tắc thì báo \`POLICY_NOT_APPROVED\`/giữ Draft hoặc từ chối chuyển trạng thái nghiệp vụ quan trọng, **không tự áp giá trị giả**.
- Định dạng UI: ngày dd/MM/yyyy; API khuyến nghị ISO 8601; thời điểm có timezone; tiền lưu Decimal/int, không float. Ký tự tiếng Việt giữ nguyên Unicode; chuẩn hóa chuỗi để so trùng cần quyết định quy tắc canonical.
- **Thông điệp lỗi** hiển thị theo field, giữ dữ liệu người dùng đã nhập (trừ dữ liệu nhạy cảm); không tiết lộ bản ghi khác pháp nhân. Mã lỗi áp dụng theo tài liệu 14.

## 2. Hồ sơ nhân viên và pháp nhân
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường, quyền, trigger | Mã lỗi/hiện trạng |
|---|---|---|---|
| Employee.id | R; khóa kỹ thuật bất biến | Không dùng CCCD làm PK; không tái cấp | SPEC \`IMMUTABLE_ID\` |
| Employee.staff_code | R khi Active; varchar(50) theo DE-VN-EMP-001 | U theo phạm vi pháp nhân hoặc toàn hệ thống **cần chốt**; trim, chống mã rỗng/trùng | SPEC \`EMP_CODE_DUPLICATE\` |
| Employee.full_name | R khi Active; chuỗi Unicode, không trắng toàn bộ | Quy tắc tách họ/tên trên Horilla cần mapping bảo toàn | SPEC \`REQUIRED\` |
| Employee.date_of_birth | Theo loại lao động và hồ sơ | Không cho ngày tương lai; tuổi tối thiểu/nhóm lao động theo POLICY | SPEC \`INVALID_DOB\` |
| EmploymentAssignment.company_id | R, FK; có phạm vi tenant | Không lấy pháp nhân trực tiếp từ client khi chưa kiểm tra quyền; lịch sử điều chuyển | SPEC \`TENANT_SCOPE_DENIED\` |
| EmploymentAssignment.department_id, position_id, location_id | Điều kiện theo tổ chức | FK thuộc pháp nhân, còn hiệu lực ở ngày bắt đầu | SPEC \`REFERENCE_NOT_EFFECTIVE\` |
| EmploymentAssignment.valid_from/to | R từ ngày, đến nullable; to >= from | Không có khoảng phân công chính trái phép chồng lấn; đổi công ty bằng sự kiện riêng | SPEC \`EFFECTIVE_DATE_OVERLAP\` |
| LegalEntity.code | R; varchar(32); U theo domain doanh nghiệp | Chuẩn hóa mã, không tái sử dụng | SPEC \`CODE_DUPLICATE\` |
| LegalEntity.tax_id | Theo loại pháp nhân; dữ liệu nhạy cảm | Chính sách kiểm tra mẫu, định danh/chi nhánh, uniqueness cần Pháp chế chốt | POLICY \`TAX_ID_INVALID\` |
| LegalEntity.legal_name | R; Unicode, max255 theo data dictionary | Đối chiếu pháp nhân với thông tin hợp đồng | SPEC \`REQUIRED\` |
| WorkLocation.province_code, commune_code | R nếu thuộc lãnh thổ VN; FK danh mục có hiệu lực | Không suy từ địa danh text; mapping hành chính theo ngày | SPEC \`ADMIN_CODE_INVALID\` |
| WorkLocation.minimum_wage_zone | R khi dùng kiểm tra lương tối thiểu | Chọn theo địa điểm và văn bản hiệu lực, có phiên bản | POLICY \`WAGE_ZONE_UNRESOLVED\` |

## 3. VNEmployeeLegalProfile — model đã bổ sung
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| employee | R; OneToOne Employee; PROTECT | 1 hồ sơ VN hiện hành/nhân viên; lịch sử thay đổi pháp lý cần entity khác | CODE |
| company | R; FK Company; PROTECT | Phải khớp company trong employee_work_info khi được gán | CODE; thiếu effective dating |
| nationality | Char(2); mặc định VN | Quy tắc ISO, quốc tịch đôi, hiệu lực cần quyết định | CODE độ dài; SPEC danh mục |
| citizen_id_suffix | Optional; chính xác 4 chữ số nếu có | Không nhận CCCD nguyên ở đây; hiển thị mask và audit | CODE \`INVALID_SUFFIX\` |
| citizen_id_vault_ref | Optional; Char(200), không thuần số/không whitespace | Chỉ chấp nhận opaque vault token; kiểm tra tồn tại/ACL của vault khi tích hợp | CODE cú pháp; SPEC vault |
| tax_id_suffix / social_insurance_suffix | Optional; đúng 4 chữ số nếu có | Giữ riêng định danh, chỉ mask; không xuất raw | CODE |
| tax_id_vault_ref / social_insurance_vault_ref | Optional; Char(200), opaque, không whitespace/thuần số | Vault chưa tích hợp | CODE cú pháp; SPEC vault |
| residency_type | Enum unverified / resident / nonresident, default unverified | Trước tính PIT phải có căn cứ xác minh và ngày áp dụng; không suy đoán cư trú | CODE enum; SPEC effective date |
| verification_status | Enum pending / verified, default pending | Khi verified cần verifier, evidence, verified_at, audit; hiện chưa đủ liên trường | CODE enum; GAP |
| verified_at | Nullable datetime | Không để verified_at trong tương lai; bắt buộc khi verified theo SPEC | SPEC chưa có |
| notes | Optional text | Không nhập nguyên CCCD/MST/BHXH, thông tin nhạy cảm vào ghi chú | SPEC cần kiểm soát PII |

## 4. VNDependent — người phụ thuộc
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| employee, company | R; FK/PROTECT | Công ty khớp phân công nhân viên | CODE |
| full_name | R; Char(200) | Trim/NFC, không chỉ khoảng trắng; cách tìm trùng không dựa duy nhất tên | CODE độ dài; SPEC normalize |
| relationship | R; Char(40) tự do | TO-BE cần danh mục quan hệ chuẩn và giá trị khác có lý do | GAP so với Data Dictionary enum |
| birth_date | Nullable Date | Không ở tương lai, kiểm tra theo nhóm đối tượng phụ thuộc | SPEC/POLICY |
| identity_suffix | Optional; 4 chữ số nếu có | Không sử dụng để quyết định trùng duy nhất | CODE |
| identity_vault_ref | Optional; Char(200), opaque token | Kho dữ liệu bảo mật chưa có | CODE cú pháp; SPEC tích hợp |
| eligible_from | R; Date | Ngày bắt đầu tính điều kiện; đối chiếu luật, ngày đăng ký, ngày xác minh | CODE kiểu; POLICY thuế |
| eligible_to | Nullable Date >= eligible_from | Không cho khoảng quyền lợi mâu thuẫn nếu cùng người/NLĐ | CODE thứ tự; SPEC overlap |
| verification_status | pending / verified / rejected | Khi verified phải có cơ sở; rejected cần reason và người quyết định | CODE enum; SPEC workflow |
| evidence_ref | Optional; Char(200) | Chỉ tham chiếu chứng cứ qua quyền tải tệp, không URL công khai | CODE field; SPEC storage |
| created_at | auto timestamp | Ghi audit thay đổi trạng thái/hiệu lực | CODE; SPEC event history |

## 5. VNContractAmendment — phụ lục hợp đồng
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| company, contract | R; FK/PROTECT | Company khớp nhân viên của hợp đồng | CODE; SPEC khoảng hợp đồng hiệu lực |
| amendment_code | R; Char(64), U(company, code) | Không cho chuỗi rỗng sau trim; quy tắc mã theo pháp nhân | CODE unique; SPEC trim |
| effective_date | R; Date | Cần kiểm tra HĐ gốc, phụ lục trùng thời điểm, kỳ Paid, tác động hồi tố | CODE field; GAP workflow |
| new_monthly_wage_vnd | R; Decimal(17,0); >=0 | Kiểm tra lương tối thiểu theo phạm vi/địa điểm và thời điểm; 0 có hợp lệ hay không cần quyết định | CODE >=0; POLICY min wage |
| status | draft / approved; default draft | Chỉ chuyển draft→approved; không tạo approved trực tiếp qua UI | CODE |
| created_by / approved_by | FK nullable | Khi approved bắt buộc approved_by, khác created_by nếu created_by có giá trị; SPEC bắt buộc created_by | CODE một phần |
| approved_at | datetime nullable | Bắt buộc khi approved, không tự nhập bằng client | CODE |
| notes | Optional | Nêu lý do điều chỉnh/hồi tố, tài liệu có quyền riêng | SPEC |
| approved amendment | không sửa đè sau duyệt | Cần sự kiện áp dụng lên hợp đồng và payroll snapshot, chưa có | CODE freeze; GAP integration |

## 6. VNAttendanceCorrection — đề nghị sửa công
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| company, employee | R, FK | Kiểm tra employee thuộc company theo ngày công, không duyệt chéo scope | SPEC chưa thấy clean company/employee |
| work_date | R, Date | Xác định theo lịch ca (không tự lấy ngày checkout), kỳ công khóa cần luồng khác | CODE field; SPEC guard |
| requested_minutes | R, Integer từ -1440 đến 1440 | Cần chốt nghĩa nghiệp vụ là delta phút hay tổng phút, và giới hạn theo ca | CODE range; POLICY |
| reason | R, nonblank sau trim | Min/max nội dung, lọc dữ liệu nhạy cảm; yêu cầu chứng từ theo case | CODE nonblank; SPEC |
| status | pending / approved / rejected | Không chỉnh sau khi xử lý | CODE |
| requested_by | nullable FK trong model | SPEC phải có actor có quyền; tự duyệt bị cấm | CODE admin gán; GAP null |
| reviewed_by / reviewed_at | Bắt buộc khi status != pending | Người duyệt khác requested_by nếu có | CODE |
| source_log_id, before/after, evidence_ref | Chưa có trong model | Cần để truy vết log gốc, thời gian điều chỉnh và kết quả | GAP cần bổ sung trước integration |
| attendance_period_lock | Chưa có trong model | Nếu đã khóa phải qua request điều chỉnh kỳ / delta payroll | GAP |

## 7. VNLeaveLedgerEntry — giao dịch số dư phép
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| id | UUID auto PK | ID bất biến | CODE |
| company, employee, leave_type | R; FK/PROTECT | Cần xác minh employee và leave_type đúng pháp nhân và còn hiệu lực | GAP cross-reference |
| source_key | R; Char(120); U(company, source_key) | Idempotency key sự kiện; định dạng nguồn và loại sự kiện thống nhất | CODE unique; SPEC namespace |
| effective_date | R; Date | Nếu kỳ đóng cần transaction bù, không ghi lùi tùy tiện | CODE field; SPEC lock |
| units | R; Decimal(9,2), !=0 | Chính sách đơn vị ngày/giờ, số âm là debit; cấm vượt mức nếu rule yêu cầu | CODE nonzero; SPEC/POLICY |
| reason | R; nonblank | Bắt buộc có lý do và nguồn quyết định | CODE |
| created_at | auto timestamp | Không ghi đè; audit, source_request_id/correlation_id cần chuẩn hóa | CODE timestamp; GAP ref |
| edit/delete | Bị chặn ở instance save/delete | QuerySet bulk/update/delete và DB direct write phải có rào chắn riêng | CODE instance; GAP enforcement |

## 8. VNRuleSet — bộ công thức động
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| company | R; FK/PROTECT | Rule chỉ phục vụ pháp nhân được cấp quyền | CODE superuser-only Admin |
| code | R; Slug(64) | Unique cùng company+version; không nhầm code rule set với mã biến trong biểu thức | CODE unique composite |
| version | positive integer; default 1 | U(company, code, version); thứ tự supersession theo ngày hiệu lực | CODE |
| title | R; Char(200) | Không trống, mô tả rõ phạm vi/chính sách | CODE field |
| status | draft/review/approved/retired | Người lập khác người duyệt; approved immutable, retired không sửa | CODE |
| effective_from | R, Date | Không được có 2 bộ approved cùng company/code cùng ngày bắt đầu | CODE |
| effective_to | Nullable Date >= from | Xử lý khoảng hiệu lực nhiều version còn thiếu policy cho trường hợp rỗng/giao nhau | CODE thứ tự; SPEC |
| legal_reference | Text | Khi approved phải khác trống, cần reference phiên bản và nguồn có thể xác minh | CODE require approve; POLICY review |
| parameters | JSON object tối đa 80; key regex lower_snake, value Decimal-compatible; không dùng reserved names | Không cho input override tham số | CODE |
| input_names | JSON array tối đa 80, unique; key lower_snake, không trùng parameter/function | Tất cả declared input phải hiện diện khi preview | CODE |
| golden_cases | JSON array tối đa 50; mỗi case có inputs, expected không rỗng | Khi approve phải có case và mọi expected line phải bằng kết quả | CODE; thiếu test coverage matrix nghiệp vụ |
| created_by/approved_by/approved_at | Trước approved phải đủ và maker != checker | Không cho tự duyệt | CODE |
| approved immutability | Các trường chính không sửa đè; approved→retired | Theo vòng đời và effective rule | CODE; Admin action retired chưa đưa vào actions |

## 9. VNPayRule — dòng công thức
| Field | Bắt buộc/kiểu/ràng buộc | Liên trường/quyền/trigger | Hiện trạng |
|---|---|---|---|
| rule_set | R FK | Chỉ sửa khi rule_set draft | CODE |
| position | PositiveInt; U(rule_set, position) | Các dòng tính theo thứ tự, không forward reference | CODE |
| code | lower_snake regex; U(rule_set, code) | Không trùng tham số/input/function | CODE |
| label | R; Char(200) | Có nhãn giải thích tiếng Việt, không lộ PII | CODE field |
| category | earning/subtotal/tax/insurance_employee/insurance_employer/deduction/net | Mapping vào payslip chính thức chưa có | CODE enum; GAP adapter |
| expression | R; 1–700 ký tự, AST <=100 node, độ sâu runtime <=20; các hàm whitelist | Chặn token nguy hiểm, biến chưa khai báo, chia 0, kết quả quá giới hạn; dùng Decimal | CODE |
| explanation | Optional Text | Nêu căn cứ, nguồn input và rounding/điều kiện | CODE field; SPEC quality |
| round_vnd | ROUND_HALF_UP về 1 đồng | Thứ tự và thời điểm làm tròn từng khoản theo policy đã duyệt | CODE function; POLICY |
| preview inputs | JSON object với đúng input_names; không thừa/thiếu; số ở dạng numeric-string/int | Preview không ghi Payslip; input thật không đưa vào log | CODE |

## 10. Các thực thể AS-IS/TO-BE khác phải khóa schema trước khi code
| Nhóm | Trường cần đặc tả ở SRS/Data Dictionary | Validation tối thiểu, chưa được coi là CODE |
|---|---|---|
| HĐLĐ | contract_type, number, signed_at, start_at, end_at, wage, work_location | required theo loại HĐ; end>=start; U số HĐ theo pháp nhân; overlap theo policy; mức lương tối thiểu hiệu lực |
| Ca/lịch | shift_start/end, break_minutes, work_date_rule, roster_version, schedule_from/to | Ca qua ngày; giờ nghỉ hợp lệ; phiên bản lịch; không hai phân ca trái policy |
| Chấm công gốc | source, external_event_id, happened_at_utc, device_id, employee_id, event_type | U(source,event_id); timestamp valid; mapping nhân viên; không update log gốc |
| OT | request_start/end, actual_start/end, approved_minutes, classification, multiplier_version | end>start; không overlap trả trùng; giới hạn thời gian/đối tượng theo POLICY |
| Đơn nghỉ | leave_type, start/end, part_of_day, requested_units, balance, evidence, approver | end>=start; no overlap; tính theo lịch; leave entitlement; rule khóa kỳ |
| Payroll batch | company, period_from/to, pay_date, tax_date, attendance_lock_version, rule_set_id | 1 kỳ active theo scope; hợp đồng/công/rule hiệu lực; idempotency |
| Payslip/PayLine | employee, run_id, code, amount_vnd, category, rule_version, source_id, hash | đối soát gross/net, tiền theo Decimal, nguồn trace đầy đủ, immutable sau Paid |
| Bank payout | bank_code, account_ref, payee_name, bank_ref, amount_vnd, state | kiểm tra tài khoản trong vault; checksum, reject/partial settlement, không Paid dựa vào xuất file |
| SecurityGrant | user, role, company, department, field_scope, valid_from/to | deny-by-default, không cross tenant, ủy quyền có thời hạn, audit |

## 11. Yêu cầu implementation/test bắt buộc
Mỗi trường trước khi Ready cho Dev phải có: ID DE; tab/màn hình; nhãn; datatype/storage; null/default; visible/editable theo status/role; client/server/API/import validation; phụ thuộc liên trường; thời gian hiệu lực; dữ liệu nhạy cảm; error_code+message; test valid/invalid/boundary/permission/duplicate/concurrent; vị trí model/form/serializer; quyết định nghiệp vụ và người duyệt. Không gắn nhãn DONE nếu thiếu một mục hoặc chưa được phân loại NOT_APPLICABLE có lý do.

Liên kết: [UC chi tiết](12-USE-CASE-DETAILS.md), [workflow](13-WORKFLOW-STATE-TRANSITIONS.md), [phân quyền/mã lỗi](14-API-PERMISSION-ERROR-CONTRACT.md), [traceability/QA](15-TRACEABILITY-UAT-MATRIX.md).
