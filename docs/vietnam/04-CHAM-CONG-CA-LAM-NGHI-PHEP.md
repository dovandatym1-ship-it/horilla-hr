# VN-HRM | Đặc tả nghiệp vụ ca làm, chấm công, làm thêm và nghỉ phép
**Mã:** VNHRM-OPS-04 · **Phiên bản:** 1.0 · **Trạng thái:** Dự thảo · **Epic:** E-VN-04 · **Feature:** F-VN-008/009/010

## 1. AS-IS và mục tiêu TO-BE
Đã đọc `base/models.py` (EmployeeShift, Roster), `attendance/models.py` (Attendance, AttendanceActivity, AttendanceConflictResolution, AttendanceOverTime), `leave/models.py` (LeaveType, AvailableLeave, LeaveRequest), `payroll/methods/payslip_calc.py` (phân loại OT theo ngày). Horilla có cấu trúc tương ứng nhưng chưa đủ cơ sở để khẳng định kết quả phù hợp quy tắc tiền lương/ca đêm của Việt Nam. TO-BE giữ log chấm công, lịch và quyết định công tách biệt.

## 2. Dữ liệu đầu vào bắt buộc
Pháp nhân; địa điểm; lịch làm việc phiên bản; ngày hiệu lực; phân ca theo nhân viên; loại ngày (ngày làm việc/nghỉ hằng tuần/nghỉ lễ/nghỉ bù/nghỉ có lương); log nguồn check-in/out; request giải trình; nghỉ được duyệt; OT đăng ký, duyệt và giờ thực tế; kỳ công; người chốt công. Dữ liệu có thời gian phải có timezone và `source_id`.

## 3. Cấu hình ca và công chuẩn
### 3.1. Định nghĩa
- **Ca ngày/ca đêm/ca qua ngày:** khoảng có `shift_start`, `shift_end`, `work_date_rule`, nghỉ giữa ca, giờ tính công và cách khấu trừ break. Ca 22:00–06:00 có ngày bắt đầu khác ngày check-out.
- **Ngày công chuẩn:** suy ra từ lịch áp dụng và lịch nghỉ riêng của từng pháp nhân/nhân viên trong kỳ; không gắn cố định 26 ngày hoặc 30 ngày cho mọi kỳ.
- **Lịch công bố:** có ngày hiệu lực, ngày ban hành và người duyệt; thay đổi lịch hồi tố tạo phiên bản và thông báo tác động.
- **Loại công:** đủ công, nửa công, vắng có phép, vắng không phép, công chưa hợp lệ, nghỉ lễ, nghỉ bù, đi công tác, làm tại nhà (nếu chính sách), ca chuyển đổi.

### 3.2. Quy tắc
**BR-OPS-001:** một log chấm công có định danh duy nhất theo hệ thống nguồn; gửi lại không tạo lần chấm công nhân đôi.  
**BR-OPS-002:** ghép log vào ca theo cửa sổ được duyệt; đi qua 00:00 không mặc định tạo 2 ngày công.  
**BR-OPS-003:** thiếu in/out và log không khớp gán trạng thái `exception`; không tự điền giờ ảo.  
**BR-OPS-004:** chỉnh công giữ log gốc và bản điều chỉnh, có `requested_by`, `approved_by`, lý do.  
**BR-OPS-005:** thời gian nghỉ giữa ca tính/không tính giờ làm theo luật, quy chế và loại ca; không tự mặc định.  
**BR-OPS-006:** số giờ công chuẩn/hưởng lương/OT/không hưởng lương là các số độc lập và cộng đối soát theo kỳ.

## 4. Làm thêm giờ (OT)
**Phân loại chiều thứ nhất:** ngày làm việc bình thường, ngày nghỉ hằng tuần, ngày nghỉ lễ/tết, ngày nghỉ có hưởng lương theo trường hợp luật định. **Chiều thứ hai:** ban ngày/ban đêm; **chiều thứ ba:** ngoài giờ theo lịch/ngày nghỉ; **chiều thứ tư:** tình trạng duyệt và loại đơn. Từ khóa `regular`, `week_off`, `holiday` là nhãn đầu vào, không phải tỷ lệ tiền cố định.

### 4.1. Luồng
1. Nhân viên/Manager tạo đề nghị OT trước hoặc sau ca theo chính sách; lưu công việc, khoảng thời gian, điểm làm việc.
2. Hệ thống kiểm tra điều kiện giới hạn theo căn cứ pháp lý có hiệu lực (thời lượng/ngày/tháng/năm và trường hợp ngoại lệ) và quy chế.
3. Người có thẩm quyền phê duyệt; nếu vi phạm điều kiện pháp lý thì chặn hoặc gắn ngoại lệ cần xử lý, không tự bỏ kiểm tra.
4. Lấy thời gian thực tế từ kết quả công đã xác nhận, giao với khoảng OT được duyệt theo chính sách; không trả tiền trên số giờ yêu cầu chưa làm.
5. Phân đoạn khoảng OT tại ranh giới ngày, ca đêm, ngày lễ/nghỉ; áp rule tương ứng với từng phân đoạn, tránh trả trùng.
6. Kết quả trả về `minutes`, `classifications`, `base_rate`, `multiplier_components`, `rule_id/version`, `amount` và người duyệt.

### 4.2. Các lỗi bắt buộc ngăn ngừa
- Ngày nghỉ trùng ngày lễ có thứ tự phân loại không được xử lý tùy tiện; dùng rule phê duyệt và tình huống pháp lý cụ thể.
- Làm thêm ban đêm cần thành phần bổ sung khác OT ban ngày; không được chỉ nhân 1 hệ số phẳng cho tất cả tình huống.
- Ca bắt đầu ngày thường, kết thúc ngày lễ: tách khoảng tại 00:00 nếu luật và lịch yêu cầu; đồng thời giữ `work_date` và tổng thời gian.
- OT bị duyệt lại, chấm công bị sửa hoặc trả lương trước đó: tính delta qua điều chỉnh, không cộng trùng.

## 5. Quản lý nghỉ phép theo ledger
### 5.1. Danh mục loại nghỉ đề xuất
Phép năm, nghỉ việc riêng hưởng lương, nghỉ không lương, nghỉ ốm, nghỉ thai sản/chế độ BH, nghỉ bù, nghỉ lễ/tết, nghỉ kết hôn/tang theo trường hợp, nghỉ công tác/khác theo doanh nghiệp. Loại nghỉ phải gắn `pay_treatment` (hưởng 100%, một phần, không hưởng, do BH chi trả hoặc loại khác), `balance_policy`, `evidence_requirement`, `approval_chain` và `statutory_basis`; **không** suy mọi loại nghỉ có trong danh mục đều là khoản doanh nghiệp phải trả.

### 5.2. Sổ cái số dư phép
Số dư cuối = số dư đầu + cấp phép/tích lũy + phép được chuyển + điều chỉnh tăng − nghỉ đã duyệt − hết hạn − điều chỉnh giảm. Đơn vị ngày/giờ phải đồng nhất; mỗi giao dịch mang `event_id` unique, `source_request`, `effective_date` và dấu audit. Khi request từ chối hoặc rút trước khi duyệt thì không debit. Nếu duyệt rồi hủy đúng điều kiện thì credit đúng một lần, không xóa lịch sử.

### 5.3. Tính phép
Đầu vào: điều kiện làm việc, thời gian làm việc, số tháng đủ điều kiện, thâm niên, thời điểm vào/nghỉ việc, ca/giờ làm, các thời gian được tính là thời gian làm việc theo luật, số dư chuyển và giới hạn chính sách. **Không hardcode 12 ngày/năm cho mọi đối tượng**; cấu hình quyền lợi pháp định theo nhóm công việc và hiệu lực, rồi cộng chính sách công ty nếu có lợi hơn khi phù hợp. Tỷ lệ phép kỳ chưa đủ năm và phép tăng theo thâm niên phải có bảng quyết định được HR/pháp chế duyệt.

### 5.4. Luồng request
Nháp → kiểm tra lịch, trùng ngày, số dư dự kiến → nộp → duyệt nhiều cấp (nếu cấu hình) → số dư debit & đồng bộ bảng công → có thể hủy/điều chỉnh qua transaction độc lập. Nếu bảng công/kỳ lương đã chốt thì mở yêu cầu điều chỉnh thay vì tự thay kết quả Paid.

## 6. Chốt bảng công
Bảng đối soát hàng nhân viên và ngày gồm: lịch gán, công chuẩn, giờ vào/ra thực tế, giờ công xác nhận, đi muộn/về sớm, OT theo loại, loại nghỉ, trạng thái duyệt, tác động payroll, nguồn và ghi chú. Tổng hợp theo nhân viên: công chuẩn, công hưởng lương, vắng không lương, nghỉ hưởng chế độ, OT phê duyệt, ngoại lệ chưa giải quyết. Chỉ HR được phân quyền chốt; quản lý ký xác nhận hoặc theo cơ chế được duyệt. Một lần chốt sinh `attendance_period_version` với hash danh sách nguồn, thời điểm và người chốt.

## 7. Ma trận tình huống kiểm thử
| TC | Dữ liệu vào | Kỳ vọng |
|---|---|---|
| TC-ATT-001 | 2 log y hệt cùng external ID | Chỉ lưu 1 sự kiện, 1 công |
| TC-ATT-002 | Nhân viên yêu cầu sửa giờ ra, sau đó HR duyệt | Log gốc vẫn còn; công mới có link đến quyết định |
| TC-ATT-003 | Không có log out | Ngoại lệ chưa duyệt; không tự tạo 8h |
| TC-ATT-004 | Ca 22:00 thứ Ba → 06:00 thứ Tư | Một ca, được phân bổ và hiển thị đúng |
| TC-ATT-005 | Chốt công khi còn request sửa chưa giải quyết | Block hoặc theo ngưỡng ngoại lệ đã duyệt; có log |
| TC-OT-001 | 2 loại allowance trùng giờ OT | Giờ được tính một lần, có source trace |
| TC-OT-002 | OT xuyên đêm và trùng ranh giới ngày lễ | Tách segment và đúng rule hiệu lực |
| TC-OT-003 | Request OT 3h, thực làm 2h | Tiền tính theo nguồn xác nhận và chính sách giao cắt |
| TC-LEV-001 | Nghỉ 1/2 ngày có ca 6h | Số dư và công đúng đơn vị chính sách |
| TC-LEV-002 | Approve request hai lần do retry | Chỉ trừ phép một lần |
| TC-LEV-003 | Carryforward hết hạn | Có bút toán hết hạn, không đổi lịch sử debit |
| TC-LEV-004 | Đã trả lương rồi yêu cầu sửa phép | Adjustment workflow, không ghi đè phiếu Paid |
| TC-LEV-005 | Nghỉ ốm hưởng chế độ BH | Không tự mặc định 100% doanh nghiệp trả |
| TC-LEV-006 | NV vào giữa năm và có thâm niên | Prorate và accrual theo rule được ký duyệt |

## 8. Bất đồng cần chốt
**DEC-OPS-01** giờ chốt ngày công ca đêm; **02** ngày nghỉ theo pháp nhân và vùng; **03** OT sau ca có duyệt hồi tố hay không; **04** công chuẩn cho nhóm ca luân phiên; **05** loại nghỉ có/không hưởng lương và cơ quan chi trả; **06** quy chế phép chuyển năm; **07** công tác/remote; **08** quy trình mở khóa kỳ công; **09** cách quy đổi phần ngày/giờ; **10** phân quyền duyệt chéo.

**Căn cứ cần đối chiếu:** Bộ luật Lao động 45/2019/QH14 và Nghị định 145/2020/NĐ-CP với các văn bản sửa đổi, hướng dẫn và quy chế nội bộ hiệu lực tại ngày áp dụng. Thông số tiền, giờ giới hạn chính thức chỉ cấu hình sau khi xác nhận luật.


## 9. Phụ lục OPS v1.1 — Validation và workflow chuẩn
**Nguồn dữ liệu quyết định:** WorkCalendarVersion + raw log immutable + công hiệu lực + request correction/OT/leave approved + AttendancePeriodLockVersion. Giờ công, OT approved và số dư phép là các đại lượng riêng, không tự suy từ giờ check-in/out. Các trường thời gian phải tách nguồn UTC, múi giờ hiển thị và work_date của ca qua đêm.

- **Correction**: \`VNAttendanceCorrection.requested_minutes\` hiện nhận -1440..1440; ý nghĩa delta/tổng giờ chưa có quyết định. Khi approved ở PR #3, trạng thái lưu trên model nhưng **chưa** cập nhật Attendance gốc. Cần source log, before/after, evidence, reviewer, kỳ khóa và apply idempotent.
- **Leave ledger**: \`VNLeaveLedgerEntry\` chỉ append-only qua instance và unique \`(company,source_key)\`; không tự trừ \`AvailableLeave\`. Chốt đơn vị ngày/giờ, accrual, debit/credit, balance âm, carryforward và vòng đời cancellation trước khi tích hợp.
- **OT**: chỉ phát tiền dựa trên giao của request approved với giờ thực tế xác nhận; phân đoạn theo ngày, ca đêm và loại ngày. Giới hạn/tỷ lệ cần phiên bản căn cứ được HR/Pháp chế duyệt; không nhập tỷ lệ hardcode vào SRS.
- **Close attendance**: Không chốt khi thiếu ngoại lệ quan trọng; phải tạo snapshot/version/hash và người chốt; chỉnh sau Paid chuyển delta kỳ sau.

Chi tiết [validation từng field](10-FIELD-LEVEL-VALIDATION-MATRIX.md), [UC](12-USE-CASE-DETAILS.md), [WF](13-WORKFLOW-STATE-TRANSITIONS.md), [UAT](15-TRACEABILITY-UAT-MATRIX.md).
