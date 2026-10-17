# Đặc tả phân quyền, an toàn dữ liệu và báo cáo HRM Việt Nam
**Mã:** VNHRM-SEC-07 · **Phiên bản:** 1.0 · **Trạng thái:** TO-BE/Draft · **Ngày:** 17/10/2026

## 1. Kiến trúc quyền bốn lớp
**L1: Xác thực** — phiên người dùng/SSO/JWT, khóa tài khoản và thu hồi phiên. **L2: RBAC chức năng** — view/create/edit/approve/export/close. **L3: Data scope** — chính mình, nhân viên trực thuộc, phòng ban, pháp nhân, hoặc quyền đặc biệt có thời hạn. **L4: Field scope** — phân quyền đến CCCD, MST, BHXH, ngân hàng, lương, người phụ thuộc và các chứng từ nhạy cảm.

**AS-IS đã đọc:** horilla_auth; horilla_api/authentication.py dùng TenantScopedJWTAuthentication; base/horilla_company_manager.py; horilla_audit; report/registry.py. Đây là nền tảng có thể dùng lại, KHÔNG chứng minh mọi endpoint hiện tại đã ngăn được truy cập trái quyền; phải kiểm tra theo từng hành vi.

## 2. Ma trận tối thiểu
| Dữ liệu/chức năng | NLĐ | Quản lý | HR | Payroll | Người duyệt lương | Finance | Admin kỹ thuật |
|---|---|---|---|---|---|---|---|
| Hồ sơ cơ bản | bản thân | nhân viên thuộc cấp | theo đơn vị | trường cần thiết | theo quyền | — | cấu hình |
| CCCD, BHXH, MST | mask bản thân | — | quyền nhạy cảm | quyền nhạy cảm | mask | mask | — |
| HĐLĐ | bản thân | khi được cấp | soạn/sửa | đọc dữ liệu lương | duyệt theo phân công | đọc theo nhiệm vụ | — |
| Chấm công và nghỉ | bản thân | xem/duyệt team | sửa/chốt | đọc để tính lương | tổng hợp | — | — |
| Thành phần lương | phiếu của mình | — | — | soạn/xem | duyệt | chi trả và đối soát | — |
| Tính/duyệt bảng lương | — | — | — | lập/tính thử | phê duyệt | ghi nhận thanh toán | — |
| Báo cáo | bản thân | tổng hợp team | phòng ban | theo pháp nhân | theo quyền | theo nhiệm vụ | — |
| Audit | lịch sử của mình có hạn chế | — | theo quyền | theo quyền | theo quyền | theo quyền | kiểm toán được cấp |

Admin kỹ thuật không mặc nhiên có quyền đọc dữ liệu lương. Người lập lương và người phê duyệt phải được phân tách khi chính sách SoD yêu cầu.

## 3. Business Rules bảo mật
- BR-SEC-001: Mọi CRUD/list/search/export/detail/download đều thực thi tenant scope ở server, kể cả relation lookup và truy vấn trong thống kê.
- BR-SEC-002: ID của pháp nhân khác trong URL/body/query không được đọc, sửa, duyệt hoặc tiết lộ bản ghi có tồn tại.
- BR-SEC-003: Không có quyền xem lương thì dashboard, API, CSV/XLSX, PDF, báo cáo pivot/drilldown cũng không được lộ số tiền.
- BR-SEC-004: Chỉ HR/Payroll được phân công nhìn thông tin định danh nhạy cảm; log truy cập và xuất thông tin có thời gian, actor, mục đích, phạm vi và số bản ghi.
- BR-SEC-005: Không ghi token, CCCD, tài khoản ngân hàng đầy đủ và mật khẩu trong error log, audit hoặc URL.
- BR-SEC-006: Offboarding phải khóa quyền đúng ngày hiệu lực; logout/password reset làm mất khả năng tiếp tục phiên theo cơ chế ứng dụng.
- BR-SEC-007: Ủy quyền phê duyệt phải có người cấp, người nhận, phạm vi, ngày bắt đầu/kết thúc, lý do; không thể chuyển quyền trái pháp nhân.
- BR-SEC-008: Truy xuất đính kèm bằng đường dẫn dự đoán không được bypass quyền; backup/restore cũng phải bảo vệ tệp nhạy cảm.
- BR-SEC-009: Nếu phải sử dụng quyền khẩn cấp (break-glass), cần phê duyệt, thời hạn và kiểm toán sau hành động.
- BR-SEC-010: Nhân viên rời công ty không được tiếp tục truy cập bằng refresh token và liên kết tải phiếu lương cũ không còn được chia sẻ vô hạn.

## 4. Quản lý dữ liệu cá nhân
Căn cứ cần được DPO/Pháp chế thẩm định: Luật 91/2025/QH15 và Nghị định 356/2025/NĐ-CP hiệu lực 01/01/2026. Lập bảng xử lý cho mỗi loại dữ liệu: nguồn, mục đích, căn cứ, ai xem, ai nhận, thời hạn, nơi lưu, rủi ro, quyền của chủ thể, cơ chế đáp ứng yêu cầu. Không tự mặc định mọi nghiệp vụ quản lý lao động đều cần consent theo một cách giống nhau. Dữ liệu sinh trắc học, sức khỏe và dữ liệu thành viên gia đình phải đánh giá riêng.

## 5. Danh mục báo cáo và chuẩn xuất
| ID | Tên báo cáo | Nhóm dữ liệu | Quyền |
|---|---|---|---|
| RPT-VN-001 | Danh sách nhân sự | mã, tên, đơn vị, chức danh, HĐ, trạng thái | HR/scope |
| RPT-VN-002 | Biến động nhân sự | vào, chuyển, nghỉ, kỳ | HR/scope |
| RPT-VN-003 | Hợp đồng hết hạn | số, hạn, trạng thái xử lý | HR |
| RPT-VN-004 | Bảng chấm công | ngày công chuẩn, công hưởng lương, OT, ngoại lệ | HR/Manager |
| RPT-VN-005 | Số dư phép năm | đầu, cấp, dùng, hết hạn, cuối | HR |
| RPT-VN-006 | Bảng lương chi tiết | earnings, BH NLĐ, BH DN, PIT, Net | Payroll |
| RPT-VN-007 | Chi phí nhân sự | tổng chi phí công ty theo kỳ/bộ phận | Finance |
| RPT-VN-008 | Đối soát bảo hiểm | căn cứ, tỷ lệ, số tiền, tăng giảm | Payroll/Finance |
| RPT-VN-009 | Báo cáo thuế TNCN | thu nhập tính thuế, giảm trừ, khấu trừ | Payroll |
| RPT-VN-010 | File chi trả ngân hàng | tài khoản, số tiền, trạng thái chuyển | Finance |
| RPT-VN-011 | Nhật ký điều chỉnh | actor, trước/sau, lý do | Kiểm toán |

Chuẩn: dd/MM/yyyy, VND nguyên, Unicode Excel/PDF, escape công thức khi xuất CSV/XLSX, gắn mã biểu mẫu/version, tổng bằng các dòng, chỉ xuất trong data scope. Danh mục trên là biểu mẫu nội bộ, KHÔNG khẳng định đủ mẫu nộp BHXH/thuế chính thức.

## 6. Các kênh tích hợp
- Máy chấm công: ID thiết bị, mã nhân viên, thời điểm UTC, chống log trùng, hàng đợi lỗi và đối soát.
- Excel import: dry-run, preview, kiểm tra từng dòng, import idempotent, log lỗi, không ghi đè ngoài ý muốn.
- Ngân hàng: xuất file theo mẫu từng ngân hàng được duyệt, có checksum, người duyệt và báo cáo đối soát; không đánh dấu Paid chỉ vì đã tải file.
- Email/thông báo: không gửi CCCD/Net đầy đủ trong body; dùng liên kết phải đăng nhập.
- Cơ quan BHXH/Thuế: chưa giả định đã có API tích hợp; chỉ cung cấp export có kiểm soát trong MVP.

## 7. TC bắt buộc
TC-SEC-001: role A gửi employee ID thuộc company B qua API không xem/sửa được.  
TC-SEC-002: xem dashboard lương khi không có quyền thì số tiền phải được loại bỏ cả trong JSON.  
TC-SEC-003: người tạo bảng lương cố tự duyệt bị chặn theo cấu hình.  
TC-SEC-004: export CCCD ghi đủ audit nhưng không lưu CCCD nguyên trong log.  
TC-SEC-005: offboarding ngăn truy cập qua JWT refresh.  
TC-SEC-006: tệp CSV có cell bắt đầu dấu bằng không thực thi công thức.  
TC-SEC-007: tải đính kèm bằng URL không hợp lệ bị từ chối.  
TC-SEC-008: người dùng quản trị hạ tầng không tự có quyền xem phiếu lương.

**Go/No-Go:** Không còn lỗi truy cập chéo pháp nhân; đã có biên bản kiểm thử RBAC, field-masking, export, restore; nghiệp vụ xử lý dữ liệu cá nhân có phê duyệt.
