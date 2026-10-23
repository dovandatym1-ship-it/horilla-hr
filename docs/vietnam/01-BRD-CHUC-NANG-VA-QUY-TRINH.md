# VN-HRM | BRD: phạm vi chức năng và quy trình nghiệp vụ
**Mã:** VNHRM-BRD-01 · **Phiên bản:** 1.0 · **Trạng thái:** Dự thảo · **Baseline:** Horilla 2.0

## 1. Bối cảnh, vấn đề, mục tiêu
Horilla là HRMS mã nguồn mở có module về nhân viên, tuyển dụng, công, phép và lương. Doanh nghiệp Việt Nam cần dữ liệu định danh/pháp lý, cơ cấu tổ chức, hồ sơ lao động, công theo lịch và quy chế, lương–thuế–bảo hiểm theo hiệu lực, phân quyền nhiều pháp nhân, xuất biểu mẫu tiếng Việt. Kết quả mong muốn: một nguồn dữ liệu chuẩn từ **hợp đồng → lịch → công/nghỉ → lương → phê duyệt → báo cáo**, truy nguyên được sự kiện và người chịu trách nhiệm.

**KPI chấp nhận đề xuất:** 100% phiếu lương mẫu UAT đối soát đến đơn vị đồng; không có truy cập chéo pháp nhân; 100% nghiệp vụ khóa kỳ có log; mỗi yêu cầu có TC; không mất dữ liệu/hợp đồng khi chạy migration. Chỉ tiêu đo hiệu năng và SLA cần được phê duyệt sau baseline.

## 2. Stakeholders và ranh giới trách nhiệm
**Ban giám đốc:** xem tổng hợp, duyệt chính sách; **HR:** chủ hồ sơ, tổ chức, hợp đồng, nghỉ; **Quản lý:** duyệt OT/phép, giải trình; **Kế toán:** chủ quy tắc/đối soát tiền lương, thuế, bảo hiểm; **Pháp chế:** duyệt căn cứ và hiệu lực; **CNTT:** an ninh, tích hợp, backup; **NLĐ:** ESS, tự khai và tra cứu. Tác nhân ngoài: máy chấm công, ngân hàng, cơ quan BHXH, cơ quan thuế; MVP xuất tệp kiểm soát, không giả định tích hợp chính thức.

## 3. Ma trận GAP có dẫn chứng mã nguồn
| Miền | Nền Horilla AS-IS đã thấy | GAP/TO-BE | Mã |
|---|---|---|---|
| Pháp nhân, tổ chức | `base/models.py: Company, Department, JobPosition, EmployeeShift, Roster` | Mã pháp nhân/MST/địa chỉ phân cấp mới; hiệu lực vị trí/vùng lương | F-VN-004 |
| Nhân viên | `employee/models.py: Employee, EmployeeWorkInformation, EmployeeBankDetails` | CCCD, MST, mã BHXH, loại cư trú, người phụ thuộc, hồ sơ nhạy cảm có thời hạn | F-VN-005/006 |
| Tuyển dụng | `recruitment/models.py: Recruitment, Stage, Candidate` | Đề nghị tuyển, offer tiếng Việt, hồ sơ đầu vào và quyền dữ liệu ứng viên | P1 |
| Tiếp nhận | `onboarding/models.py: OnboardingTask, CandidateStage` | Checklist tham gia BH, ký HĐ, cấp tài khoản, bàn giao thiết bị | P1 |
| HĐLĐ | `payroll/models/models.py: Contract` | Loại HĐ, phụ lục, hiệu lực/ưu tiên, thử việc, lịch sử lương, cảnh báo pháp lý | F-VN-007 |
| Lịch công | `base/models.py: EmployeeShift, RotatingShift, Roster` | Lịch hiệu lực, phân ca qua ngày, đổi ca, công chuẩn, nghỉ giữa ca | F-VN-008 |
| Chấm công | `attendance/models.py: Attendance, AttendanceOverTime, AttendanceConflictResolution` | Phân tách log thô, kết quả đã duyệt, nghỉ/OT, chốt bảng công | F-VN-008/009 |
| Nghỉ | `leave/models.py: LeaveType, AvailableLeave, LeaveRequest` | Cấp phép/thâm niên/nghỉ đặc thù, lịch sử số dư, tác động payroll | F-VN-010 |
| Tính lương | `payroll/methods/payroll_run.py`, `payslip_calc.py`, `payroll_batch.py` | Adapter quy tắc VN, snapshot, thuế/bảo hiểm theo thời gian | F-VN-011…015 |
| Báo cáo | `report/registry.py`, `report/models.py` | Tờ trình công/lương, file ngân hàng, phiếu lương, đối soát | F-VN-016/017 |
| Người dùng | `horilla_auth`, `horilla_api/authentication.py` | Role + quyền dữ liệu theo công ty/phòng ban và field salary, export | F-VN-018/019 |
| Nghỉ việc | `offboarding/models.py: OffboardingEmployee, ResignationLetter` | Báo trước, bàn giao, quyết toán, ngừng quyền, lưu chứng cứ | P1 |

Đây là đánh giá **theo mã nguồn tĩnh**, không phải xác nhận các chức năng UI đã vận hành đúng.

## 4. Quy trình nghiệp vụ cấp E2E
### BP-01 Tuyển dụng → nhân viên
(1) Quản lý đề nghị nhu cầu, HR xác nhận định biên → (2) Tuyển chọn và duyệt offer → (3) Chuẩn bị hồ sơ và xác thực các trường bắt buộc → (4) Tạo nhân viên bằng mã nội bộ ổn định; đối chiếu trùng CCCD/MST có phân quyền → (5) Gán pháp nhân, đơn vị, chức danh, nơi làm việc, hợp đồng hiệu lực → (6) Thiết lập lịch/ca, tham gia BH nếu đủ điều kiện → (7) Cấp tài khoản và quyền → (8) Nhân viên xác nhận thông tin. Ngoại lệ: nhận việc sau đầu kỳ, chưa hoàn tất định danh, nhiều hợp đồng giao nhau, offer bị hủy, trùng hồ sơ. Không tự gộp dữ liệu khi phát hiện trùng.

### BP-02 Quản lý hợp đồng
Soạn nháp HĐ → kiểm tra thông tin pháp nhân/nhân viên/loại HĐ/ngày hiệu lực → kiểm tra xung đột và quyền sửa → HR/đại diện được phân công phê duyệt → lưu số, ngày ký, phiên bản và đính kèm → kích hoạt theo thời gian → phụ lục/gia hạn/điều chuyển/chấm dứt có sự kiện lịch sử. Thay đổi mức lương không sửa đè bản ghi HĐ lịch sử; bảng lương mỗi kỳ truy xuất hợp đồng hiệu lực của kỳ.

### BP-03 Lập lịch → chấm công
HR cấu hình địa điểm, ca, ngày nghỉ, lịch làm việc/roster và công chuẩn → nhân viên chấm công từ thiết bị/web → lưu log gốc và nguồn → ghép vào ngày công theo lịch/qua đêm → phát hiện đi muộn, thiếu log, trùng log, vị trí không hợp lệ → nhân viên giải trình → quản lý/HR duyệt sửa theo phân quyền → phân loại ngày công/OT/điều chỉnh → đối soát nghỉ đã duyệt → chốt bảng công kỳ.

### BP-04 Đề nghị nghỉ và quản lý số dư
Nhân viên xem số dư dự kiến → chọn loại nghỉ và thời gian → hệ thống tính số ngày ảnh hưởng theo lịch hiệu lực, nửa ngày/qua kỳ → kiểm tra quyền lợi, xung đột với công, điều kiện minh chứng → gửi duyệt → duyệt hoặc từ chối → ghi ledger tăng/giảm số dư, điều chỉnh lịch và công → ghi lại hoàn phép khi hủy hợp lệ. Không trừ số dư hai lần khi duyệt lại request.

### BP-05 Công → lương → thanh toán
Tạo kỳ lương, chọn pháp nhân/nhân viên → kiểm tra HĐ đang hiệu lực và công đã chốt → tạo dữ liệu đầu vào theo snapshot → tính lương cơ bản/OT/phụ cấp/nghỉ hưởng lương/giảm trừ → tính nghĩa vụ bảo hiểm nhân viên/doanh nghiệp riêng → phân loại tính thuế, giảm trừ, TNCN → đối soát ngoại lệ (thiếu công, Net âm, dữ liệu pháp lý thiếu, thay đổi retroactive) → Trình duyệt → Phê duyệt → Chốt → xuất phiếu và file chi trả → xác nhận thanh toán → khóa kết quả. Không sửa trạng thái Paid trở lại Draft; điều chỉnh ghi kỳ bổ sung.

### BP-06 Điều chuyển hoặc nghỉ việc
Tiếp nhận đề nghị → xác định loại chấm dứt, báo trước/theo trường hợp → HR kiểm tra công nợ, tài sản, ngày hiệu lực → bàn giao và phê duyệt → chốt công/tiền nghỉ phép/nghĩa vụ tài chính → báo tăng/giảm bảo hiểm theo quy trình kiểm soát → chặn quyền đăng nhập theo ngày hiệu lực → lưu bằng chứng, chính sách retention và audit.

## 5. Sự kiện và trạng thái chuẩn
| Đối tượng | Trạng thái đề xuất | Không được làm |
|---|---|---|
| Hồ sơ nhân viên | Draft → Active → Suspended/Offboarded/Archived | Xóa cứng hồ sơ có bảng lương |
| Hợp đồng | Draft → Pending Approval → Active → Expired/Terminated | Hai hợp đồng lương đang áp dụng trái rule không được giải quyết |
| Đơn nghỉ | Draft → Submitted → Pending → Approved/Rejected/Cancelled | Trừ phép hai lần; xóa đơn đã chi trả |
| Phiếu sửa công | Submitted → Approved/Rejected | Sửa log gốc không có dấu vết |
| Bảng công | Open → Reconciled → Locked → Reopened (có lý do + version) | Payroll dùng công chưa chốt |
| Kỳ lương | Draft → Review → Approved → Paid/Cancelled | Quay lùi kỳ đã Paid; sửa trực tiếp số tiền đã Paid |
| Điều chỉnh lương | Draft → Approved → Applied | Thay lịch sử bằng update-in-place |

Các trạng thái có sẵn của Horilla khác nhau theo model; bảng trên là **TO-BE** và cần mapping rõ trước khi code.

## 6. Luật chung bất biến
- Pháp nhân và nhân viên là khóa dữ liệu không được tự suy từ URL; mọi API truy xuất qua tenant scoping và object-level permission.
- Không có hợp đồng/lịch/quy tắc hiệu lực tại một ngày ⇒ phát sinh ngoại lệ, không chọn bản gần nhất một cách âm thầm.
- Mỗi sự kiện điều chỉnh có actor, source, timestamp, lý do, before/after, ID tham chiếu; phải có phương án undo có kiểm soát khi chưa Paid.
- Bảng lương đã Paid là immutable đối với số đã chi, thay đổi được thể hiện bằng truy lĩnh/truy thu có kỳ ghi nhận và kỳ gốc.
- Mọi công thức phụ thuộc luật phải dùng version của kỳ áp dụng và quyết định cho trường hợp hồi tố, không dùng ngày tính máy chủ làm mặc định không rõ ràng.

## 7. Phê duyệt quyết định và acceptance
**DEC-VN-001**: xác định đối tượng triển khai (1 hoặc nhiều pháp nhân); **002**: quy chế công chuẩn/tháng; **003**: lịch ca, nghỉ bù; **004**: kỳ lương & ngày trả lương; **005**: tiền ngoài lương chịu thuế/BH; **006**: tính Gross/Net và quy tắc làm tròn; **007**: chính sách điều chỉnh sau Paid; **008**: phân quyền khoản nhạy cảm; **009**: hồ sơ/chứng từ cần lưu; **010**: pháp chế ký duyệt rule 2026.

**Nghiệm thu BRD:** ký duyệt luồng E2E, bảng trạng thái, danh sách GAP và DEC; gắn UC/TC chi tiết tại các tài liệu kế tiếp.

## 8. Phụ lục BRD v1.1 — Điểm giao nhận và phạm vi nghiệm thu
Các BP-01..06 phía trên là **process map cấp cao**, không phải BPMN/UC đủ cho dev. Chi tiết trigger, state/action guard, nhánh nghiệp vụ và bù trừ được định nghĩa trong [WF-13](13-WORKFLOW-STATE-TRANSITIONS.md), [UC-12](12-USE-CASE-DETAILS.md).

**Điều kiện bàn giao từng bước:** BP-01 giao Employee Active kèm pháp nhân có hiệu lực; BP-02 giao Contract+Amendment version, không ghi đè quá khứ; BP-03 giao Attendance Locked và correction decision có source; BP-04 giao ledger đã đối soát; BP-05 chỉ dùng snapshot/ruleset approved để tính, phiếu Paid immutable; BP-06 giao ngày nghỉ, quyết toán và xác nhận thu hồi quyền. Giao thiếu → tạo exception có owner, không tự chuyển bước.

**Acceptance business:** HR duyệt dữ liệu nhân sự/HĐ/công/phép; Payroll/Finance duyệt đối soát tiền; Pháp chế duyệt legal rule/effective date; Security duyệt quyền dữ liệu, vault. Chưa có sign-off trên tài liệu này. Quy tắc chưa chốt trong [GAP-16](16-CODE-TO-DOC-GAP.md) phải giữ OPEN/BLOCKED_BY_POLICY.
